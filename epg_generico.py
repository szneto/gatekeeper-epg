import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from xml.dom import minidom

# Canais e seus IDs
canais = {
    "TOPTV": "TOP TV HD",
    "TVT": "TVT HD",
    "MaisFamilia": "Rede Mais Família HD"
}

# Função para gerar o EPG
def gerar_epg(canais, dias=5):
    # Cria o elemento raiz do XML
    tv = ET.Element("tv", attrib={"generator-info-name": "none", "generator-info-url": "none"})
    
    # Adiciona os canais ao XML
    for canal_id, nome_canal in canais.items():
        channel = ET.SubElement(tv, "channel", id=canal_id)
        display_name = ET.SubElement(channel, "display-name", lang="pt")
        display_name.text = nome_canal
    
    # Data inicial (hoje à meia-noite)
    data_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Para cada canal, gera programas de 1 hora de duração por 5 dias
    for canal_id, nome_canal in canais.items():
        for dia in range(dias):
            data_atual = data_inicio + timedelta(days=dia)
            for hora in range(0, 24):
                inicio = data_atual + timedelta(hours=hora)
                fim = inicio + timedelta(hours=1)
                
                # Formata as datas no formato exigido pelo XMLTV
                inicio_str = inicio.strftime("%Y%m%d%H%M%S %z")
                fim_str = fim.strftime("%Y%m%d%H%M%S %z")
                
                # Cria o elemento programa
                programa = ET.SubElement(tv, "programme", channel=canal_id, start=inicio_str, stop=fim_str)
                title = ET.SubElement(programa, "title", lang="pt")
                title.text = f"Programação {nome_canal}"
    
    # Converte o XML para uma string formatada
    xml_str = ET.tostring(tv, encoding="UTF-8")
    xml_pretty = minidom.parseString(xml_str).toprettyxml(indent="  ", encoding="UTF-8")
    
    # Escreve o arquivo XML formatado
    with open("epg.xml", "wb") as f:
        f.write(xml_pretty)

# Executa a função para gerar o EPG
gerar_epg(canais)

print("EPG gerado com sucesso!")