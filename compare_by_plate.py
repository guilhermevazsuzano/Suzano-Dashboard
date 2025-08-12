import json

# Caminhos dos arquivos
SP_FILE = r"C:\Users\guilhermevaz\OneDrive - Suzano S A\Documentos\Suzano-Dashboard\sharepoint_fixed.json"
CREARE_SAMPLE = r"C:\Users\guilhermevaz\OneDrive - Suzano S A\Documentos\Suzano-Dashboard\samples\creare_sample_20250811_180128.json"

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def extract_sp_plates(data):
    # Extrai placas de todas as listas SharePoint
    plates = set()
    for lst in data.get("lists", {}).values():
        for item in lst:
            # ajuste o campo conforme sua estrutura
            plate = item.get("vehiclePlate") or item.get("placa") or item.get("Veiculo")
            if plate:
                plates.add(plate)
    return plates

def extract_creare_plates(data):
    # Extrai placas da amostra Creare
    events = data.get("sample_events") or data.get("sampleEvents") or data.get("events") or []
    return { ev.get("vehiclePlate") for ev in events if ev.get("vehiclePlate") }

def main():
    sp = load_json(SP_FILE)
    cr = load_json(CREARE_SAMPLE)

    sp_plates = extract_sp_plates(sp)
    cr_plates = extract_creare_plates(cr)

    common = sp_plates & cr_plates
    only_sp = sp_plates - cr_plates
    only_cr = cr_plates - sp_plates
    coverage = len(common) / len(sp_plates) * 100 if sp_plates else 0

    print(f"SharePoint plates: {len(sp_plates)}")
    print(f"Creare plates:     {len(cr_plates)}")
    print(f"Plates in common:  {len(common)}")
    print(f"Only in SP:        {len(only_sp)}")
    print(f"Only in Creare:    {len(only_cr)}")
    print(f"Coverage (%):      {coverage:.1f}%\n")

    print("Examples in common:", list(common)[:5])
    print("Examples only in SP:", list(only_sp)[:5])
    print("Examples only in Creare:", list(only_cr)[:5])

if __name__ == "__main__":
    main()

