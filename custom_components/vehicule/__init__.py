"""
Integrarea Vehicule pentru Home Assistant.

Gestionarea vehiculelor, documentelor și notificărilor pentru expirări.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import voluptuous as vol
from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import (
    async_track_point_in_time,
    async_track_time_interval,
)
from homeassistant.util import dt as dt_util

from .const import (
    BACKUP_VERSION,
    CATEGORII_ARHIVABILE,
    CONF_CASCO_COMPANIE,
    CONF_CASCO_COST,
    CONF_CASCO_DATA_EMITERE,
    CONF_CASCO_DATA_EXPIRARE,
    CONF_CASCO_NUMAR_POLITA,
    CONF_ISTORIC,
    CONF_ITP_DATA_EXPIRARE,
    CONF_ITP_KILOMETRAJ,
    CONF_ITP_STATIE,
    CONF_KM_CURENT,
    CONF_NR_INMATRICULARE,
    CONF_RCA_COMPANIE,
    CONF_RCA_COST,
    CONF_RCA_DATA_EMITERE,
    CONF_RCA_DATA_EXPIRARE,
    CONF_RCA_NUMAR_POLITA,
    CONF_ROVINIETA_CATEGORIE,
    CONF_ROVINIETA_DATA_INCEPUT,
    CONF_ROVINIETA_DATA_SFARSIT,
    CONF_ROVINIETA_PRET,
    DOMAIN,
    LICENSE_DATA_KEY,
    PLATFORMS,
    SERVICE_ACTUALIZEAZA_CASCO,
    SERVICE_ACTUALIZEAZA_DATE,
    SERVICE_ACTUALIZEAZA_ITP,
    SERVICE_ACTUALIZEAZA_RCA,
    SERVICE_ACTUALIZEAZA_ROVINIETA,
    SERVICE_EXPORTA_DATE,
    SERVICE_IMPORTA_DATE,
    normalizeaza_numar,
)
from .helpers import aplatizeaza_optiuni, ro_la_iso, structureaza_optiuni
from .license import LicenseManager

_LOGGER = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Scheme pentru servicii
# ─────────────────────────────────────────────

SCHEMA_ACTUALIZEAZA_DATE = vol.Schema(
    {
        vol.Required(CONF_NR_INMATRICULARE): cv.string,
        vol.Required(CONF_KM_CURENT): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=9_999_999)
        ),
    }
)

SCHEMA_EXPORTA_DATE = vol.Schema(
    {
        vol.Required(CONF_NR_INMATRICULARE): cv.string,
    }
)

SCHEMA_IMPORTA_DATE = vol.Schema(
    {
        vol.Required("cale_fisier"): cv.string,
    }
)

# ─── Serviciu: actualizează rovinieta ───

SCHEMA_ACTUALIZEAZA_ROVINIETA = vol.Schema(
    {
        vol.Required(CONF_NR_INMATRICULARE): cv.string,
        vol.Optional("data_inceput"): cv.string,
        vol.Optional("data_sfarsit"): cv.string,
        vol.Optional("categorie"): cv.string,
        vol.Optional("pret"): vol.All(
            vol.Coerce(float), vol.Range(min=0, max=99999)
        ),
        vol.Optional("arhivare", default=False): cv.boolean,
    }
)

# ─── Serviciu: actualizează ITP ───

SCHEMA_ACTUALIZEAZA_ITP = vol.Schema(
    {
        vol.Required(CONF_NR_INMATRICULARE): cv.string,
        vol.Optional("data_expirare"): cv.string,
        vol.Optional("statie"): cv.string,
        vol.Optional("kilometraj"): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=9_999_999)
        ),
        vol.Optional("arhivare", default=False): cv.boolean,
    }
)

# ─── Serviciu: actualizează RCA ───

SCHEMA_ACTUALIZEAZA_RCA = vol.Schema(
    {
        vol.Required(CONF_NR_INMATRICULARE): cv.string,
        vol.Optional("numar_polita"): cv.string,
        vol.Optional("companie"): cv.string,
        vol.Optional("data_emitere"): cv.string,
        vol.Optional("data_expirare"): cv.string,
        vol.Optional("cost"): vol.All(
            vol.Coerce(float), vol.Range(min=0, max=99999)
        ),
        vol.Optional("arhivare", default=False): cv.boolean,
    }
)

# ─── Serviciu: actualizează CASCO ───

SCHEMA_ACTUALIZEAZA_CASCO = vol.Schema(
    {
        vol.Required(CONF_NR_INMATRICULARE): cv.string,
        vol.Optional("numar_polita"): cv.string,
        vol.Optional("companie"): cv.string,
        vol.Optional("data_emitere"): cv.string,
        vol.Optional("data_expirare"): cv.string,
        vol.Optional("cost"): vol.All(
            vol.Coerce(float), vol.Range(min=0, max=99999)
        ),
        vol.Optional("arhivare", default=False): cv.boolean,
    }
)


# ─────────────────────────────────────────────
# Setup / Unload
# ─────────────────────────────────────────────


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configurează o intrare pentru un vehicul."""
    _LOGGER.debug(
        "[Vehicule] Setup entry_id=%s (%s)",
        entry.entry_id,
        entry.data.get(CONF_NR_INMATRICULARE),
    )

    hass.data.setdefault(DOMAIN, {})

    # ── Inițializare License Manager (o singură instanță per domeniu) ──
    if LICENSE_DATA_KEY not in hass.data.get(DOMAIN, {}):
        _LOGGER.debug("[Vehicule] Inițializez LicenseManager (prima entry)")
        license_mgr = LicenseManager(hass)
        # IMPORTANT: setăm referința ÎNAINTE de async_load() pentru a preveni
        # race condition-ul: async_load() face await HTTP, ceea ce cedează
        # event loop-ul. Fără această ordine, alte entry-uri concurente ar vedea
        # LICENSE_DATA_KEY ca lipsă și ar crea câte un LicenseManager duplicat,
        # generând N request-uri /check simultane (câte unul per vehicul).
        hass.data[DOMAIN][LICENSE_DATA_KEY] = license_mgr
        await license_mgr.async_load()
        _LOGGER.debug(
            "[Vehicule] LicenseManager: status=%s, valid=%s, fingerprint=%s...",
            license_mgr.status,
            license_mgr.is_valid,
            license_mgr.fingerprint[:16],
        )

        # Heartbeat periodic — intervalul vine de la server (via valid_until)
        interval_sec = license_mgr.check_interval_seconds
        _LOGGER.debug(
            "[Vehicule] Programez heartbeat periodic la fiecare %d secunde (%d ore)",
            interval_sec,
            interval_sec // 3600,
        )

        async def _heartbeat_periodic(_now) -> None:
            """Verifică statusul la server dacă cache-ul a expirat.

            Logică:
            1. Captează is_valid ÎNAINTE de heartbeat
            2. Dacă cache expirat → contactează serverul
            3. Captează is_valid DUPĂ heartbeat
            4. Dacă starea s-a schimbat → reload entries (tranziție curată)
            5. Reprogramează heartbeat-ul la intervalul actualizat de server
            """
            mgr: LicenseManager | None = hass.data.get(DOMAIN, {}).get(
                LICENSE_DATA_KEY
            )
            if not mgr:
                _LOGGER.debug("[Vehicule] Heartbeat: LicenseManager nu există, skip")
                return

            # Captează starea ÎNAINTE de heartbeat
            was_valid = mgr.is_valid

            if mgr.needs_heartbeat:
                _LOGGER.debug("[Vehicule] Heartbeat: cache expirat, verific la server")
                await mgr.async_heartbeat()

                # Captează starea DUPĂ heartbeat
                now_valid = mgr.is_valid

                # Detectează tranziții pe care async_check_status nu le-a prins
                # (ex: server inaccesibil + cache expirat → is_valid devine False)
                if was_valid and not now_valid:
                    _LOGGER.warning(
                        "[Vehicule] Licența a devenit invalidă — reîncarc senzorii"
                    )
                    await mgr._async_reload_entries()
                elif not was_valid and now_valid:
                    _LOGGER.info(
                        "[Vehicule] Licența a redevenit validă — reîncarc senzorii"
                    )
                    await mgr._async_reload_entries()

                # Reprogramează heartbeat-ul la intervalul actualizat de server
                new_interval = mgr.check_interval_seconds
                _LOGGER.debug(
                    "[Vehicule] Heartbeat: reprogramez la %d secunde (%d min)",
                    new_interval,
                    new_interval // 60,
                )
                # Oprește vechiul timer
                cancel_old = hass.data.get(DOMAIN, {}).get("_cancel_heartbeat")
                if cancel_old:
                    cancel_old()
                # Programează noul timer cu intervalul actualizat
                cancel_new = async_track_time_interval(
                    hass,
                    _heartbeat_periodic,
                    timedelta(seconds=new_interval),
                )
                hass.data[DOMAIN]["_cancel_heartbeat"] = cancel_new
            else:
                _LOGGER.debug("[Vehicule] Heartbeat: cache valid, nu e nevoie de verificare")

        cancel_heartbeat = async_track_time_interval(
            hass,
            _heartbeat_periodic,
            timedelta(seconds=interval_sec),
        )
        hass.data[DOMAIN]["_cancel_heartbeat"] = cancel_heartbeat
        _LOGGER.debug("[Vehicule] Heartbeat programat și stocat în hass.data")

        # ── Timer precis la valid_until (zero gap la expirare cache) ──
        def _schedule_cache_expiry_check(mgr_ref: LicenseManager) -> None:
            """Programează un check EXACT la momentul expirării cache-ului.

            Elimină complet fereastra dintre expirarea cache-ului și
            următorul heartbeat periodic. La expirare, contactează
            serverul imediat și declanșează reload dacă starea se schimbă.
            """
            # Anulează timer-ul anterior (dacă există)
            cancel_prev = hass.data.get(DOMAIN, {}).pop(
                "_cancel_cache_expiry", None
            )
            if cancel_prev:
                cancel_prev()

            valid_until = (mgr_ref._status_token or {}).get("valid_until")
            if not valid_until or valid_until <= 0:
                return

            expiry_dt = dt_util.utc_from_timestamp(valid_until)
            # Adaugă 2 secunde ca marjă (evită race condition cu cache check)
            expiry_dt = expiry_dt + timedelta(seconds=2)

            async def _on_cache_expiry(_now) -> None:
                """Callback executat EXACT la expirarea cache-ului."""
                mgr_now: LicenseManager | None = hass.data.get(
                    DOMAIN, {}
                ).get(LICENSE_DATA_KEY)
                if not mgr_now:
                    return

                was_valid = mgr_now.is_valid
                _LOGGER.debug(
                    "[Vehicule] Cache expirat — verific imediat la server"
                )
                await mgr_now.async_check_status()
                now_valid = mgr_now.is_valid

                if was_valid != now_valid:
                    if now_valid:
                        _LOGGER.info(
                            "[Vehicule] Licența a redevenit validă — reîncarc"
                        )
                    else:
                        _LOGGER.warning(
                            "[Vehicule] Licența a devenit invalidă — reîncarc"
                        )
                    await mgr_now._async_reload_entries()

                # Programează următorul check (dacă serverul a dat valid_until nou)
                _schedule_cache_expiry_check(mgr_now)

            cancel_expiry = async_track_point_in_time(
                hass, _on_cache_expiry, expiry_dt
            )
            hass.data[DOMAIN]["_cancel_cache_expiry"] = cancel_expiry

            _LOGGER.debug(
                "[Vehicule] Cache expiry timer programat la %s",
                expiry_dt.isoformat(),
            )

        _schedule_cache_expiry_check(license_mgr)

        # ── Notificare re-enable (dacă a fost dezactivată anterior) ──
        was_disabled = hass.data.pop(f"{DOMAIN}_was_disabled", False)
        if was_disabled:
            await license_mgr.async_notify_event("integration_enabled")

        if not license_mgr.is_valid:
            _LOGGER.warning(
                "[Vehicule] Integrarea nu are licență validă. "
                "Senzorii vor afișa 'Licență necesară'."
            )
        elif license_mgr.is_trial_valid:
            _LOGGER.info(
                "[Vehicule] Perioadă de evaluare — %d zile rămase",
                license_mgr.trial_days_remaining,
            )
        else:
            _LOGGER.info(
                "[Vehicule] Licență activă — tip: %s",
                license_mgr.license_type,
            )
    else:
        _LOGGER.debug(
            "[Vehicule] LicenseManager există deja (entry suplimentară)"
        )

    # Stocăm referința la intrare în hass.data
    hass.data[DOMAIN][entry.entry_id] = entry

    # Înregistrăm listener-ul pentru actualizarea opțiunilor
    entry.async_on_unload(entry.add_update_listener(_async_actualizare_optiuni))

    # Configurăm platformele (senzori)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Înregistrăm serviciile (doar o dată, la primul vehicul)
    await _async_inregistreaza_servicii(hass)

    _LOGGER.debug("[Vehicule] Setup complet pentru entry_id=%s", entry.entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Descarcă o intrare (vehicul șters)."""
    _LOGGER.info(
        "[Vehicule] ── async_unload_entry ── entry_id=%s (%s)",
        entry.entry_id,
        entry.data.get(CONF_NR_INMATRICULARE),
    )

    # Descărcăm platformele
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    _LOGGER.debug("[Vehicule] Unload platforme: %s", "OK" if unload_ok else "EȘUAT")

    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        _LOGGER.debug("[Vehicule] Entry %s eliminat din hass.data", entry.entry_id)

        # Verifică dacă mai sunt entry-uri active (folosim config_entries, nu hass.data)
        entry_ids_ramase = {
            e.entry_id
            for e in hass.config_entries.async_entries(DOMAIN)
            if e.entry_id != entry.entry_id
        }

        _LOGGER.debug(
            "[Vehicule] Entry-uri rămase după unload: %d (%s)",
            len(entry_ids_ramase),
            entry_ids_ramase or "niciuna",
        )

        if not entry_ids_ramase:
            _LOGGER.info("[Vehicule] Ultima entry descărcată — curăț domeniul complet")

            # ── Eliminăm serviciile ──
            hass.services.async_remove(DOMAIN, SERVICE_ACTUALIZEAZA_DATE)
            hass.services.async_remove(DOMAIN, SERVICE_EXPORTA_DATE)
            hass.services.async_remove(DOMAIN, SERVICE_IMPORTA_DATE)
            _LOGGER.debug("[Vehicule] Serviciile au fost eliminate")

            # ── Notificare lifecycle (înainte de cleanup!) ──
            mgr = hass.data[DOMAIN].get(LICENSE_DATA_KEY)
            if mgr and not hass.is_stopping:
                if entry.disabled_by:
                    await mgr.async_notify_event("integration_disabled")
                    # Flag pentru async_setup_entry: la re-enable, trimitem "enabled"
                    hass.data[f"{DOMAIN}_was_disabled"] = True
                else:
                    # Salvăm fingerprint-ul pentru async_remove_entry
                    hass.data.setdefault(f"{DOMAIN}_notify", {}).update({
                        "fingerprint": mgr.fingerprint,
                        "license_key": mgr._data.get("license_key", ""),
                    })
                    _LOGGER.debug(
                        "[Vehicule] Fingerprint salvat pentru async_remove_entry"
                    )

            # Oprește heartbeat-ul periodic
            cancel_hb = hass.data[DOMAIN].pop("_cancel_heartbeat", None)
            if cancel_hb:
                cancel_hb()
                _LOGGER.debug("[Vehicule] Heartbeat periodic oprit")

            # Oprește timer-ul de cache expiry
            cancel_ce = hass.data[DOMAIN].pop("_cancel_cache_expiry", None)
            if cancel_ce:
                cancel_ce()
                _LOGGER.debug("[Vehicule] Cache expiry timer oprit")

            # Elimină LicenseManager
            hass.data[DOMAIN].pop(LICENSE_DATA_KEY, None)
            _LOGGER.debug("[Vehicule] LicenseManager eliminat")

            # Elimină domeniul complet
            hass.data.pop(DOMAIN, None)
            _LOGGER.debug("[Vehicule] hass.data[%s] eliminat complet", DOMAIN)

            _LOGGER.info("[Vehicule] Cleanup complet — domeniul %s descărcat", DOMAIN)
    else:
        _LOGGER.error("[Vehicule] Unload EȘUAT pentru entry_id=%s", entry.entry_id)

    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Curăță complet la ștergerea unui vehicul.

    Elimină dispozitivul și entitățile orfane din registry,
    astfel încât o readăugare ulterioară pornește de la zero.
    Dacă e ultima entry, notifică serverul de licențe.
    """
    nr_inmatriculare = entry.data.get(CONF_NR_INMATRICULARE, "")
    numar_normalizat = normalizeaza_numar(nr_inmatriculare)

    _LOGGER.debug(
        "[Vehicule] ── async_remove_entry ── entry_id=%s (%s)",
        entry.entry_id,
        nr_inmatriculare,
    )

    # ── Eliminăm entitățile din Entity Registry ──
    registru_entitati = er.async_get(hass)
    entitati_de_sters = er.async_entries_for_config_entry(
        registru_entitati, entry.entry_id
    )
    for entitate in entitati_de_sters:
        _LOGGER.debug("[Vehicule] Elimin entitatea: %s", entitate.entity_id)
        registru_entitati.async_remove(entitate.entity_id)

    # ── Eliminăm dispozitivul din Device Registry ──
    registru_dispozitive = dr.async_get(hass)
    dispozitiv = registru_dispozitive.async_get_device(
        identifiers={(DOMAIN, numar_normalizat)}
    )
    if dispozitiv is not None:
        _LOGGER.debug(
            "[Vehicule] Elimin dispozitivul: %s (id: %s)",
            dispozitiv.name,
            dispozitiv.id,
        )
        registru_dispozitive.async_remove_device(dispozitiv.id)

    _LOGGER.info("[Vehicule] Vehiculul %s a fost complet eliminat", nr_inmatriculare)

    # ── Notificare licență (doar la ultima entry) ──
    remaining = hass.config_entries.async_entries(DOMAIN)
    if not remaining:
        notify_data = hass.data.pop(f"{DOMAIN}_notify", None)
        if notify_data and notify_data.get("fingerprint"):
            await _send_lifecycle_event(
                hass,
                notify_data["fingerprint"],
                notify_data.get("license_key", ""),
                "integration_removed",
            )


async def _send_lifecycle_event(
    hass: HomeAssistant, fingerprint: str, license_key: str, action: str
) -> None:
    """Trimite un eveniment lifecycle direct (fără LicenseManager).

    Folosit în async_remove_entry când LicenseManager nu mai există.
    """
    import hashlib
    import hmac as hmac_lib
    import time

    import aiohttp
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    from .license import INTEGRATION, LICENSE_API_URL

    timestamp = int(time.time())
    payload = {
        "fingerprint": fingerprint,
        "timestamp": timestamp,
        "action": action,
        "license_key": license_key,
        "integration": INTEGRATION,
    }
    # HMAC cu fingerprint ca cheie (identic cu LicenseManager._compute_request_hmac)
    data = {k: v for k, v in payload.items() if k != "hmac"}
    import json as _json
    msg = _json.dumps(data, sort_keys=True).encode()
    payload["hmac"] = hmac_lib.new(
        fingerprint.encode(), msg, hashlib.sha256
    ).hexdigest()

    try:
        session = async_get_clientsession(hass)
        async with session.post(
            f"{LICENSE_API_URL}/notify",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=10),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Vehicule-HA-Integration/3.0",
            },
        ) as resp:
            if resp.status == 200:
                result = await resp.json()
                if not result.get("success"):
                    _LOGGER.warning(
                        "[Vehicule] Server a refuzat '%s': %s",
                        action, result.get("error"),
                    )
    except Exception as err:  # noqa: BLE001
        _LOGGER.debug("[Vehicule] Nu s-a putut raporta '%s': %s", action, err)


async def _async_actualizare_optiuni(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:
    """Reîncarcă intrarea când opțiunile se schimbă."""
    _LOGGER.debug(
        "Opțiuni actualizate pentru %s – reîncarc",
        entry.data.get(CONF_NR_INMATRICULARE),
    )
    await hass.config_entries.async_reload(entry.entry_id)


# ─────────────────────────────────────────────
# Utilitar intern: caută vehicul după nr. înmatriculare
# ─────────────────────────────────────────────


def _gaseste_vehicul(
    hass: HomeAssistant, nr_inmatriculare: str
) -> ConfigEntry | None:
    """Returnează ConfigEntry pentru vehiculul dat sau None."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.data.get(CONF_NR_INMATRICULARE) == nr_inmatriculare:
            return entry
    return None


# ─────────────────────────────────────────────
# Utilitar intern: normalizare dată pentru servicii
# ─────────────────────────────────────────────


def _normalizeaza_data(valoare: str) -> str | None:
    """Normalizează o dată primită prin serviciu la format ISO (AAAA-LL-ZZ).

    Acceptă:
    - ISO: 2026-03-12 sau 2026-03-12 09:52:47
    - RO:  12.03.2026
    Returnează data în format ISO sau None dacă e invalidă.
    """
    if not valoare or not str(valoare).strip():
        return None
    text = str(valoare).strip()
    # Dacă conține spațiu (ex: "2026-03-12 09:52:47"), păstrăm doar data
    if " " in text:
        text = text.split(" ")[0]
    return ro_la_iso(text)


# ─────────────────────────────────────────────
# Utilitar intern: arhivare date vechi pentru servicii
# ─────────────────────────────────────────────


def _arhiveaza_date_vechi(
    optiuni: dict[str, Any], categorie: str
) -> None:
    """Arhivează datele existente ale unei categorii în istoricul vehiculului.

    Folosește aceeași structură ca _salveaza_si_inchide din config_flow.
    """
    if categorie not in CATEGORII_ARHIVABILE:
        return
    campuri_categorie = CATEGORII_ARHIVABILE[categorie]
    date_vechi: dict[str, Any] = {}
    for eticheta, cheie_const in campuri_categorie.items():
        val = optiuni.get(cheie_const)
        if val is not None and val != "":
            date_vechi[eticheta] = val
    if date_vechi:
        istoric = list(optiuni.get(CONF_ISTORIC, []))
        istoric.append(
            {
                "tip": categorie,
                "data_arhivare": datetime.now().date().isoformat(),
                "date": date_vechi,
            }
        )
        optiuni[CONF_ISTORIC] = istoric


# ─────────────────────────────────────────────
# Utilitar intern: aplică câmpuri din serviciu în opțiuni
# ─────────────────────────────────────────────


def _aplica_campuri(
    optiuni: dict[str, Any],
    call_data: dict[str, Any],
    mapare: dict[str, str],
) -> None:
    """Aplică câmpurile primite prin serviciu în opțiunile vehiculului.

    Câmpurile de tip dată sunt normalizate automat la ISO.
    Câmpurile cu valoare goală sunt ignorate (nu se șterg datele existente).
    """
    campuri_data_serviciu = {"data_inceput", "data_sfarsit", "data_emitere", "data_expirare"}
    for cheie_serviciu, cheie_conf in mapare.items():
        valoare = call_data.get(cheie_serviciu)
        if valoare is None or (isinstance(valoare, str) and not valoare.strip()):
            continue
        if cheie_serviciu in campuri_data_serviciu:
            valoare_iso = _normalizeaza_data(str(valoare))
            if valoare_iso is None:
                _LOGGER.warning(
                    "Format dată invalid pentru %s: %s", cheie_serviciu, valoare
                )
                continue
            optiuni[cheie_conf] = valoare_iso
        else:
            optiuni[cheie_conf] = valoare


# ─────────────────────────────────────────────
# Înregistrare servicii
# ─────────────────────────────────────────────


async def _async_inregistreaza_servicii(hass: HomeAssistant) -> None:
    """Înregistrează serviciile domeniului (o singură dată)."""
    if hass.services.has_service(DOMAIN, SERVICE_ACTUALIZEAZA_DATE):
        return

    # ── Actualizare date (kilometraj) ──

    async def _handle_actualizeaza_date(call: ServiceCall) -> None:
        """Procesează apelul de actualizare date (kilometraj)."""
        nr_inmatriculare = call.data[CONF_NR_INMATRICULARE].strip().upper()
        km_nou = call.data[CONF_KM_CURENT]

        _LOGGER.debug(
            "Actualizez datele pentru %s – km: %d",
            nr_inmatriculare,
            km_nou,
        )

        entry = _gaseste_vehicul(hass, nr_inmatriculare)

        if entry is None:
            _LOGGER.warning(
                "Nu am găsit vehiculul cu nr. %s", nr_inmatriculare
            )
            return

        optiuni_noi: dict[str, Any] = {
            **entry.options,
            CONF_KM_CURENT: km_nou,
        }
        hass.config_entries.async_update_entry(entry, options=optiuni_noi)

    # ── Export date vehicul ──

    async def _handle_exporta_date(call: ServiceCall) -> None:
        """Exportă datele unui vehicul într-un fișier JSON.

        Fișierul se salvează în directorul config al Home Assistant:
        /config/vehicule_backup_{nr_normalizat}.json
        """
        nr_inmatriculare = call.data[CONF_NR_INMATRICULARE].strip().upper()
        nr_norm = normalizeaza_numar(nr_inmatriculare)

        entry = _gaseste_vehicul(hass, nr_inmatriculare)

        if entry is None:
            _LOGGER.warning("Export: nu am găsit vehiculul %s", nr_inmatriculare)
            persistent_notification.async_create(
                hass,
                f"Nu am găsit vehiculul cu nr. {nr_inmatriculare}.",
                title="Vehicule – Export eșuat",
                notification_id=f"vehicule_export_{nr_norm}",
            )
            return

        date_export = {
            "version": BACKUP_VERSION,
            "integration": DOMAIN,
            "nr_inmatriculare": nr_inmatriculare,
            "data_export": datetime.now().isoformat(),
            **structureaza_optiuni(dict(entry.options)),
        }

        cale = Path(hass.config.path(f"vehicule_backup_{nr_norm}.json"))

        def _scrie() -> None:
            cale.write_text(
                json.dumps(date_export, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        await hass.async_add_executor_job(_scrie)

        _LOGGER.info("Export reușit: %s → %s", nr_inmatriculare, cale)
        persistent_notification.async_create(
            hass,
            (
                f"Datele vehiculului **{nr_inmatriculare}** au fost exportate "
                f"in:\n`{cale}`"
            ),
            title="Vehicule – Export reușit",
            notification_id=f"vehicule_export_{nr_norm}",
        )

    # ── Import date vehicul ──

    async def _handle_importa_date(call: ServiceCall) -> None:
        """Importă datele unui vehicul dintr-un fișier JSON.

        Dacă vehiculul există deja, opțiunile sunt actualizate.
        Dacă vehiculul NU există, se creează automat o intrare nouă.
        """
        cale = call.data["cale_fisier"]

        # Citire fișier (I/O blocant → executor)
        def _citeste() -> dict:
            return json.loads(Path(cale).read_text(encoding="utf-8"))

        try:
            date_import = await hass.async_add_executor_job(_citeste)
        except FileNotFoundError:
            _notifica_eroare_import(hass, f"Fișierul nu a fost găsit: {cale}")
            return
        except (json.JSONDecodeError, OSError) as err:
            _notifica_eroare_import(
                hass, f"Eroare la citirea fișierului: {err}"
            )
            return

        # Validare structură de bază
        if (
            not isinstance(date_import, dict)
            or CONF_NR_INMATRICULARE not in date_import
        ):
            _notifica_eroare_import(
                hass,
                "Structura JSON este invalida. Fisierul trebuie sa contina "
                "campul 'nr_inmatriculare'.",
            )
            return

        nr = date_import[CONF_NR_INMATRICULARE].strip().upper()
        nr_norm = normalizeaza_numar(nr)

        # Detectăm formatul: v1 (flat cu „optiuni") sau v2 (structurat)
        versiune = date_import.get("version", 1)
        if versiune >= 2:
            # Format nou: categorii structurate → aplatizăm
            optiuni = aplatizeaza_optiuni(date_import)
        elif "optiuni" in date_import and isinstance(
            date_import["optiuni"], dict
        ):
            # Format vechi: opțiuni flat
            optiuni = date_import["optiuni"]
        else:
            _notifica_eroare_import(
                hass,
                "Structura JSON este invalida. Fisierul v1 trebuie sa "
                "contina campul 'optiuni'.",
            )
            return

        # Căutăm vehiculul existent
        entry = _gaseste_vehicul(hass, nr)

        if entry is None:
            # Creăm vehiculul prin import flow
            result = await hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": "import"},
                data={CONF_NR_INMATRICULARE: nr},
            )
            if result.get("type") == "create_entry":
                entry = result["result"]
            else:
                motiv = result.get("reason", "necunoscut")
                _notifica_eroare_import(
                    hass,
                    f"Nu am putut crea vehiculul {nr}: {motiv}",
                )
                return

        # Actualizăm opțiunile (listener-ul va reîncărca automat)
        hass.config_entries.async_update_entry(entry, options=optiuni)

        _LOGGER.info("Import reușit pentru %s din %s", nr, cale)
        persistent_notification.async_create(
            hass,
            f"Datele vehiculului **{nr}** au fost importate cu succes.",
            title="Vehicule – Import reușit",
            notification_id=f"vehicule_import_{nr_norm}",
        )

    # ── Actualizare rovinieta ──

    async def _handle_actualizeaza_rovinieta(call: ServiceCall) -> None:
        """Procesează apelul de actualizare rovinieta."""
        nr_inmatriculare = call.data[CONF_NR_INMATRICULARE].strip().upper()
        entry = _gaseste_vehicul(hass, nr_inmatriculare)
        if entry is None:
            _LOGGER.warning(
                "Nu am găsit vehiculul cu nr. %s", nr_inmatriculare
            )
            return

        optiuni_noi: dict[str, Any] = {**entry.options}

        # Arhivare date vechi dacă este solicitat
        if call.data.get("arhivare"):
            _arhiveaza_date_vechi(optiuni_noi, "rovinieta")

        # Mapare câmpuri serviciu → câmpuri config
        mapare = {
            "data_inceput": CONF_ROVINIETA_DATA_INCEPUT,
            "data_sfarsit": CONF_ROVINIETA_DATA_SFARSIT,
            "categorie": CONF_ROVINIETA_CATEGORIE,
            "pret": CONF_ROVINIETA_PRET,
        }
        _aplica_campuri(optiuni_noi, call.data, mapare)

        hass.config_entries.async_update_entry(entry, options=optiuni_noi)
        _LOGGER.info(
            "Rovinieta actualizată pentru %s", nr_inmatriculare
        )

    # ── Actualizare ITP ──

    async def _handle_actualizeaza_itp(call: ServiceCall) -> None:
        """Procesează apelul de actualizare ITP."""
        nr_inmatriculare = call.data[CONF_NR_INMATRICULARE].strip().upper()
        entry = _gaseste_vehicul(hass, nr_inmatriculare)
        if entry is None:
            _LOGGER.warning(
                "Nu am găsit vehiculul cu nr. %s", nr_inmatriculare
            )
            return

        optiuni_noi: dict[str, Any] = {**entry.options}

        if call.data.get("arhivare"):
            _arhiveaza_date_vechi(optiuni_noi, "itp")

        mapare = {
            "data_expirare": CONF_ITP_DATA_EXPIRARE,
            "statie": CONF_ITP_STATIE,
            "kilometraj": CONF_ITP_KILOMETRAJ,
        }
        _aplica_campuri(optiuni_noi, call.data, mapare)

        hass.config_entries.async_update_entry(entry, options=optiuni_noi)
        _LOGGER.info("ITP actualizat pentru %s", nr_inmatriculare)

    # ── Actualizare RCA ──

    async def _handle_actualizeaza_rca(call: ServiceCall) -> None:
        """Procesează apelul de actualizare RCA."""
        nr_inmatriculare = call.data[CONF_NR_INMATRICULARE].strip().upper()
        entry = _gaseste_vehicul(hass, nr_inmatriculare)
        if entry is None:
            _LOGGER.warning(
                "Nu am găsit vehiculul cu nr. %s", nr_inmatriculare
            )
            return

        optiuni_noi: dict[str, Any] = {**entry.options}

        if call.data.get("arhivare"):
            _arhiveaza_date_vechi(optiuni_noi, "rca")

        mapare = {
            "numar_polita": CONF_RCA_NUMAR_POLITA,
            "companie": CONF_RCA_COMPANIE,
            "data_emitere": CONF_RCA_DATA_EMITERE,
            "data_expirare": CONF_RCA_DATA_EXPIRARE,
            "cost": CONF_RCA_COST,
        }
        _aplica_campuri(optiuni_noi, call.data, mapare)

        hass.config_entries.async_update_entry(entry, options=optiuni_noi)
        _LOGGER.info("RCA actualizat pentru %s", nr_inmatriculare)

    # ── Actualizare CASCO ──

    async def _handle_actualizeaza_casco(call: ServiceCall) -> None:
        """Procesează apelul de actualizare CASCO."""
        nr_inmatriculare = call.data[CONF_NR_INMATRICULARE].strip().upper()
        entry = _gaseste_vehicul(hass, nr_inmatriculare)
        if entry is None:
            _LOGGER.warning(
                "Nu am găsit vehiculul cu nr. %s", nr_inmatriculare
            )
            return

        optiuni_noi: dict[str, Any] = {**entry.options}

        if call.data.get("arhivare"):
            _arhiveaza_date_vechi(optiuni_noi, "casco")

        mapare = {
            "numar_polita": CONF_CASCO_NUMAR_POLITA,
            "companie": CONF_CASCO_COMPANIE,
            "data_emitere": CONF_CASCO_DATA_EMITERE,
            "data_expirare": CONF_CASCO_DATA_EXPIRARE,
            "cost": CONF_CASCO_COST,
        }
        _aplica_campuri(optiuni_noi, call.data, mapare)

        hass.config_entries.async_update_entry(entry, options=optiuni_noi)
        _LOGGER.info("CASCO actualizat pentru %s", nr_inmatriculare)

    # ── Înregistrare efectivă ──

    hass.services.async_register(
        DOMAIN,
        SERVICE_ACTUALIZEAZA_DATE,
        _handle_actualizeaza_date,
        schema=SCHEMA_ACTUALIZEAZA_DATE,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPORTA_DATE,
        _handle_exporta_date,
        schema=SCHEMA_EXPORTA_DATE,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_IMPORTA_DATE,
        _handle_importa_date,
        schema=SCHEMA_IMPORTA_DATE,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ACTUALIZEAZA_ROVINIETA,
        _handle_actualizeaza_rovinieta,
        schema=SCHEMA_ACTUALIZEAZA_ROVINIETA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ACTUALIZEAZA_ITP,
        _handle_actualizeaza_itp,
        schema=SCHEMA_ACTUALIZEAZA_ITP,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ACTUALIZEAZA_RCA,
        _handle_actualizeaza_rca,
        schema=SCHEMA_ACTUALIZEAZA_RCA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_ACTUALIZEAZA_CASCO,
        _handle_actualizeaza_casco,
        schema=SCHEMA_ACTUALIZEAZA_CASCO,
    )
    _LOGGER.debug("Serviciile %s au fost înregistrate", DOMAIN)


def _notifica_eroare_import(hass: HomeAssistant, mesaj: str) -> None:
    """Creează o notificare persistentă pentru erori de import."""
    _LOGGER.error("Import: %s", mesaj)
    persistent_notification.async_create(
        hass,
        mesaj,
        title="Vehicule – Import eșuat",
        notification_id="vehicule_import_eroare",
    )
