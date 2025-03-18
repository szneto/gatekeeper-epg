import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
import time
import math

def fetch_json():
    url = "https://programacao.claro.com.br/gatekeeper/exibicao/select?q=id_revel:(1_2113+19_408+18_2214+20_2077+20_2091+28_1987+133_563+133_1004+133_858+133_545+133_1044+133_1420+133_1656+133_1292+319_1642+302_1177+161_2063+16_1868+16_1940+14_1899)&wt=json&rows=1000000&start=0&sort=id_canal+asc,dh_inicio+asc&fl=dh_fim dh_inicio st_titulo titulo id_programa id_canal id_cidade diretor elenco genero"
    start_date = datetime.now(timezone.utc)
    end_date = start_date + timedelta(days=5)
    
    url = url.replace("dh_inicio:[2025-3-13T00:00:00Z+TO+2025-3-17T23:59:00Z]", f"dh_inicio:[{start_date.strftime('%Y-%m-%dT00:00:00Z')}+TO+{end_date.strftime('%Y-%m-%dT23:59:00Z')}]")
    
    response = requests.get(url)
    data = response.json()
    print(f"Programas encontrados: {len(data.get('response', {}).get('docs', []))}")
    return data

def generate_generic_epg(channel_name, channel_id, root):
    start_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
    for day in range(5):
        for hour in range(24):
            start_time = start_date + timedelta(days=day, hours=hour)
            stop_time = start_time + timedelta(hours=1)
            
            prog = ET.SubElement(root, "programme", attrib={
                "start": start_time.strftime("%Y%m%d%H%M%S") + " +0000",
                "stop": stop_time.strftime("%Y%m%d%H%M%S") + " +0000",
                "channel": channel_id
            })
            ET.SubElement(prog, "title", attrib={"lang": "pt"}).text = f"Programação ({channel_name})"

def fetch_program_descriptions(channel_name, daily_programs):
    descriptions = {}
    
    for day, program_ids in daily_programs.items():
        chunk_size = 50
        chunks = [program_ids[i:i + chunk_size] for i in range(0, len(program_ids), chunk_size)]
        total_chunks = len(chunks)

        for index, chunk in enumerate(chunks, start=1):
            print(f"🔍 Buscando descrições {channel_name} - Dia {day} - Parte {index}/{total_chunks} ({len(chunk)} programas)")
            
            query = "+".join(chunk)
            url = f"https://programacao.claro.com.br/gatekeeper/prog/select?q=id_programa:({query})&start=0&wt=json&rows=100000&fl=id_programa descricao"
            
            response = requests.get(url)
            
            if response.status_code != 200 or not response.text.strip():
                print(f"⚠️ Erro na requisição para {channel_name} - Dia {day} - Parte {index}/{total_chunks} - Status: {response.status_code}")
                time.sleep(5)
                continue
            
            try:
                data = response.json()
                for item in data.get("response", {}).get("docs", []):
                    descriptions[item["id_programa"]] = item["descricao"]
            except requests.exceptions.JSONDecodeError as e:
                print(f"❌ Erro ao processar JSON para {channel_name} - Dia {day} - Parte {index}/{total_chunks}: {e}")
            
            time.sleep(5)
    
    return descriptions

def convert_to_xml(json_data):
    root = ET.Element("tv", attrib={
        "generator-info-name": "Neto Souza",
        "generator-info-url": "http://netosouza.net"
    })
    
    channels = {
        "563": "Globo-SP",
        "1004": "Record-SP",
        "858": "SBT-SP",
        "545": "Band-SP",
        "1044": "Cultura-SP",
        "1420": "Rede-TV-SP",
        "1656": "Rede-Vida",
        "1292": "Gazeta-SP",
        "2063": "TV-Clube-HD",
        "1868": "EPTV-RP",
        "1940": "SBT-RP",
        "1899": "Record-Int-SP",
        "2077": "TV-TEM-Sor",
        "2091": "TV-Sorocaba",
        "408": "Band-Campinas",
        "2214": "Record-Paulista",
        "1642": "RBI-TV",
        "2113": "Rede-Gospel",
        "1177": "TV-Aparecida",
        "1987": "TV-Evangelizar",
        "9991": "Top-TV",
        "9992": "Rede-Mais-Familia",
        "9993": "TVT"
    }
    
    for channel_id, channel_name in channels.items():
        channel = ET.SubElement(root, "channel", attrib={"id": channel_name})
        ET.SubElement(channel, "display-name", attrib={"lang": "pt"}).text = channel_name
        
        if channel_id in ["9991", "9992", "9993"]:
            generate_generic_epg(channel_name, channel_name, root)
    
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
