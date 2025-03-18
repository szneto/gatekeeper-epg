import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
import time

def fetch_json():
    url = "https://programacao.claro.com.br/gatekeeper/exibicao/select?q=id_revel:(1_435+1_2113+19_408+18_2214+20_2077+20_2091+28_1987+133_1004+133_858+133_545+133_1044+133_1420+133_1656+133_1292+319_1642+302_1177+161_2063+16_1868+16_1940+14_1899)&wt=json&rows=1000000&start=0&sort=id_canal+asc,dh_inicio+asc&fl=dh_fim dh_inicio st_titulo titulo id_programa id_canal id_cidade diretor elenco genero"
    start_date = datetime.now(timezone.utc)
    end_date = start_date + timedelta(days=5)
    
    url = url.replace("dh_inicio:[2025-3-13T00:00:00Z+TO+2025-3-17T23:59:00Z]", f"dh_inicio:[{start_date.strftime('%Y-%m-%dT00:00:00Z')}+TO+{end_date.strftime('%Y-%m-%dT23:59:00Z')}]")
    
    response = requests.get(url)
    data = response.json()
    print(f"Programas encontrados: {len(data.get('response', {}).get('docs', []))}")
    return data

def fetch_program_descriptions(program_ids):
    descriptions = {}
    chunk_size = 50
    chunks = [program_ids[i:i + chunk_size] for i in range(0, len(program_ids), chunk_size)]

    for index, chunk in enumerate(chunks, start=1):
        print(f"🔍 Buscando descrições - Parte {index}/{len(chunks)} ({len(chunk)} programas)")
        query = "+".join(chunk)
        url = f"https://programacao.claro.com.br/gatekeeper/prog/select?q=id_programa:({query})&start=0&wt=json&rows=100000&fl=id_programa descricao"
        
        response = requests.get(url)
        if response.status_code != 200 or not response.text.strip():
            print(f"⚠️ Erro na requisição - Parte {index}/{len(chunks)} - Status: {response.status_code}")
            time.sleep(1)
            continue
        
        try:
            data = response.json()
            for item in data.get("response", {}).get("docs", []):
                descriptions[item["id_programa"]] = item["descricao"]
        except requests.exceptions.JSONDecodeError as e:
            print(f"❌ Erro ao processar JSON - Parte {index}/{len(chunks)}: {e}")
        
        time.sleep(1)
    
    return descriptions

def convert_to_xml(json_data):
    root = ET.Element("tv", attrib={
        "generator-info-name": "Neto Souza",
        "generator-info-url": "http://netosouza.net"
    })
    
    channels = {
        "435": "Globo SP",
        "1004": "Record SP",
        "858": "SBT SP",
        "545": "Band SP",
        "1044": "Cultura SP",
        "1420": "Rede TV SP",
        "1656": "Rede Vida",
        "1292": "Gazeta SP",
        "2063": "TV Clube HD",
        "1868": "EPTV RP",
        "1940": "SBT RP",
        "1899": "Record Int SP",
        "2077": "TV TEM Sor",
        "2091": "TV Sorocaba",
        "408": "Band Campinas",
        "2214": "Record Paulista",
        "1642": "RBI TV",
        "2113": "Rede Gospel",
        "1177": "TV Aparecida",
        "1987": "TV Evangelizar",
    }
    
    for channel_id, channel_name in channels.items():
        channel = ET.SubElement(root, "channel", attrib={"id": channel_name})
        ET.SubElement(channel, "display-name", attrib={"lang": "pt"}).text = channel_name
    
    programme_data = json_data.get("response", {}).get("docs", [])
    programme_descriptions = fetch_program_descriptions([p["id_programa"] for p in programme_data if "id_programa" in p])
    
    for program in programme_data:
        channel_id = str(program.get("id_canal"))
        if channel_id not in channels:
            continue
        
        start = program["dh_inicio"].replace("-", "").replace(":", "").replace("T", "").replace("Z", "") + " -0300"
        stop = program["dh_fim"].replace("-", "").replace(":", "").replace("T", "").replace("Z", "") + " -0300"
        prog = ET.SubElement(root, "programme", attrib={"start": start, "stop": stop, "channel": channels[channel_id]})
        ET.SubElement(prog, "title", attrib={"lang": "pt"}).text = program.get("titulo", "Sem Título")
        
        # Adiciona a descrição apenas se existir
        if program["id_programa"] in programme_descriptions:
            sub_title_text = programme_descriptions[program["id_programa"]].strip()
            if sub_title_text:
                ET.SubElement(prog, "sub-title").text = sub_title_text

        # Adiciona créditos apenas se existir diretor ou elenco
        if "diretor" in program or "elenco" in program:
            credits = ET.SubElement(prog, "credits")
            if "diretor" in program and program["diretor"].strip():
                ET.SubElement(credits, "director").text = program["diretor"].strip()
            if "elenco" in program and program["elenco"].strip():
                for actor in program["elenco"].split(","):
                    actor_name = actor.strip()
                    if actor_name:
                        ET.SubElement(credits, "actor").text = actor_name
        
        # Adiciona categoria apenas se existir gênero
        if "genero" in program and program["genero"].strip():
            ET.SubElement(prog, "category").text = program["genero"].strip()
    
    return ET.ElementTree(root)

def save_xml(tree, filename="clarotv.xml"):
    import xml.dom.minidom
    xml_str = ET.tostring(tree.getroot(), encoding="utf-8")
    parsed_xml = xml.dom.minidom.parseString(xml_str)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(parsed_xml.toprettyxml(indent="  "))

if __name__ == "__main__":
    json_data = fetch_json()
    xml_tree = convert_to_xml(json_data)
    save_xml(xml_tree)
    print("XML salvo como clarotv.xml")
