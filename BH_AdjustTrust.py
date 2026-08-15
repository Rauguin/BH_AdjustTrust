#!/usr/bin/env python3
"""BH_AdjustTrust - Ajusta Trusts do BloodHound CE.

O collector (nxc ou bloodhound-python) grava TrustDirection/TrustType/TrustAttributes
como numero (valor cru do LDAP), mas o BloodHound CE espera string.
Sem este ajuste, importar resulta em:
  "cannot unmarshal number into Go struct field ... of type string"

Este script transforma os campos numericos para o formato esperado pelo CE.

Uso:
  BH_AdjustTrust.py <arquivo_domains.json>

Gera:
  <arquivo_domains>-fixed.json
"""

import json
import sys
from pathlib import Path

# LDAP trustDirection -> label do BloodHound CE
DIRECTION = {0: "Disabled", 1: "Inbound", 2: "Outbound", 3: "Bidirectional"}

# flags de trustAttributes (usadas quando o collector trouxe o campo)
WITHIN_FOREST = 0x20
FOREST_TRANSITIVE = 0x08
CROSS_ORGANIZATION = 0x10
TREAT_AS_EXTERNAL = 0x40
NON_TRANSITIVE = 0x01


def para_int(v):
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, str) and v.strip().lstrip("-").isdigit():
        return int(v)
    return None


def tipo_por_attributes(attr):
    if attr & WITHIN_FOREST:
        return "ParentChild"
    if attr & FOREST_TRANSITIVE:
        return "Forest"
    if attr & (CROSS_ORGANIZATION | TREAT_AS_EXTERNAL | NON_TRANSITIVE):
        return "External"
    return "Unknown"


def tipo_por_nomes(origem, destino, transitivo):
    o = (origem or "").upper().rstrip(".")
    d = (destino or "").upper().rstrip(".")
    if o and d and (o.endswith("." + d) or d.endswith("." + o)):
        return "ParentChild"
    return "Forest" if transitivo else "External"


def ajusta_trust(trust, dominio):
    mudancas = []

    direcao = para_int(trust.get("TrustDirection"))
    if direcao is not None:
        trust["TrustDirection"] = DIRECTION.get(direcao, "Unknown")
        mudancas.append(f"TrustDirection {direcao} -> {trust['TrustDirection']}")

    attr = para_int(trust.get("TrustAttributes"))

    tipo = para_int(trust.get("TrustType"))
    if tipo is not None:
        if attr is not None:
            trust["TrustType"] = tipo_por_attributes(attr)
        else:
            trust["TrustType"] = tipo_por_nomes(
                dominio, trust.get("TargetDomainName"), bool(trust.get("IsTransitive"))
            )
        mudancas.append(f"TrustType {tipo} -> {trust['TrustType']}")

    if attr is not None:
        trust["TrustAttributes"] = str(attr)
        mudancas.append(f"TrustAttributes {attr} -> \"{attr}\"")

    return mudancas


def main():
    if len(sys.argv) != 2:
        sys.exit(f"uso: python {Path(sys.argv[0]).name} <arquivo_domains.json>")

    entrada = Path(sys.argv[1])
    if not entrada.is_file():
        sys.exit(f"[-] arquivo nao encontrado: {entrada}")

    dados = json.loads(entrada.read_text(encoding="utf-8-sig"))
    dominios = dados["data"] if isinstance(dados, dict) else dados

    total = 0
    for dominio in dominios:
        nome = (dominio.get("Properties") or {}).get("name") or dominio.get("ObjectIdentifier")
        for trust in dominio.get("Trusts") or []:
            mudancas = ajusta_trust(trust, nome)
            if mudancas:
                total += 1
                alvo = trust.get("TargetDomainName", "?")
                print(f"[+] {nome} -> {alvo}: " + ", ".join(mudancas))

    saida = entrada.with_name(entrada.stem + "-fixed.json")
    saida.write_text(json.dumps(dados), encoding="utf-8")

    if total:
        print(f"[*] {total} trust(s) corrigido(s)")
    else:
        print("[*] nenhum campo numerico encontrado (arquivo ja estava ok)")
    print(f"[*] gravado: {saida}")


if __name__ == "__main__":
    main()
