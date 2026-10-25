#!/usr/bin/env python3
"""
Version para GitHub Actions: consulta el precio UNA vez, avisa por ntfy
si Flavio bajo de 75% y guarda el estado en estado.txt para no repetir avisos.
Si lo corres a mano (Run workflow), ademas manda una notificacion de PRUEBA.
"""

import json
import os
import urllib.request

MARKET_SLUG = "will-flvio-bolsonaro-win-the-2026-brazilian-presidential-election"
NTFY_TOPIC = os.environ["NTFY_TOPIC"].strip()   # viene de un "secret" de GitHub
UMBRAL = 0.75   # avisa si baja de 75%
REARME = 0.77   # se vuelve a armar si sube de 77%
ESTADO = "estado.txt"

API_URL = f"https://gamma-api.polymarket.com/markets?slug={MARKET_SLUG}"
NTFY_URL = f"https://ntfy.sh/{NTFY_TOPIC}"


def obtener_precio_si():
    req = urllib.request.Request(API_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.load(r)
    mercado = data[0] if isinstance(data, list) else data
    outcomes = mercado["outcomes"]
    precios = mercado["outcomePrices"]
    if isinstance(outcomes, str):
        outcomes = json.loads(outcomes)
    if isinstance(precios, str):
        precios = json.loads(precios)
    idx = [o.lower() for o in outcomes].index("yes")
    return float(precios[idx])


def notificar(titulo, mensaje, prioridad="urgent", tags="rotating_light"):
    req = urllib.request.Request(
        NTFY_URL,
        data=mensaje.encode("utf-8"),
        headers={"Title": titulo, "Priority": prioridad, "Tags": tags},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        print("ntfy respondio:", r.status)


def leer_estado():
    try:
        with open(ESTADO) as f:
            return f.read().strip() or "armada"
    except FileNotFoundError:
        return "armada"


def guardar_estado(valor):
    with open(ESTADO, "w") as f:
        f.write(valor)


def main():
    precio = obtener_precio_si()
    estado = leer_estado()
    print(f"Flavio: {precio:.1%} | estado: {estado}")
    print(f"Largo del topic: {len(NTFY_TOPIC)} caracteres")

    # Prueba: solo cuando se corre a mano desde Actions
    if os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch":
        notificar(
            "Prueba de alarma OK",
            f"Si ves esto, las notificaciones andan. Flavio esta en {precio:.1%}, "
            f"aviso si baja de {UMBRAL:.0%}.",
            prioridad="default",
            tags="white_check_mark",
        )

    if estado == "armada" and precio < UMBRAL:
        notificar(
            "Flavio esta bajando!",
            f"Cayo a {precio:.1%} en Polymarket (umbral {UMBRAL:.0%}).",
        )
        guardar_estado("avisada")
    elif estado == "avisada" and precio >= REARME:
        guardar_estado("armada")
        print("Alarma re-armada")
    else:
        guardar_estado(estado)


if __name__ == "__main__":
    main()
