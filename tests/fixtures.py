"""Dados fictícios de teste (apenas para validar layout; não são publicados)."""
from src.models import Carousel

SAMPLE = {
    "date_label": "14 de abril",
    "hook": "Do naufrágio do Titanic à conclusão do Projeto Genoma Humano: seis fatos que marcaram a data.",
    "events": [
        {"year": "1865", "title": "Atentado contra Abraham Lincoln", "importance": 5, "sensitivity": "alta", "era": "contemporanea",
         "summary": "O presidente dos Estados Unidos foi baleado em um teatro de Washington e morreu na manhã seguinte. O episódio ocorreu poucos dias após o fim da Guerra Civil Americana."},
        {"year": "1912", "title": "Naufrágio do RMS Titanic", "importance": 5, "sensitivity": "alta", "era": "contemporanea",
         "summary": "O transatlântico colidiu com um iceberg no Atlântico Norte durante a viagem inaugural e afundou horas depois. A tragédia levou a mudanças nas normas de segurança marítima."},
        {"year": "2003", "title": "Conclusão do Projeto Genoma Humano", "importance": 4, "sensitivity": "baixa", "era": "contemporanea",
         "summary": "Cientistas anunciaram a conclusão do sequenciamento do genoma humano, marco da biologia moderna."},
        {"year": "44 a.C.", "title": "Fato antigo com título longo para testar a quebra de linha", "importance": 2, "sensitivity": "baixa", "era": "antiguidade",
         "summary": "Texto de teste com tamanho próximo ao limite para validar o ajuste automático da fonte no slide, em duas ou três frases curtas e objetivas, sem exageros."},
        {"year": "1209", "title": "Fato medieval de teste", "importance": 3, "sensitivity": "media", "era": "medieval",
         "summary": "Resumo curto de teste."},
        {"year": "1650", "title": "Fato da era moderna de teste", "importance": 3, "sensitivity": "baixa", "era": "moderna",
         "summary": "Resumo curto de teste para a era moderna, com duas frases. Serve para checar cores."},
    ],
    "others": [
        {"year": "1385", "line": "Batalha de Aljubarrota: vitória portuguesa que consolidou a independência do reino"},
        {"year": "1760", "line": "Evento secundário de teste com uma descrição um pouco mais longa para quebrar linha"},
        {"year": "1945", "line": "Evento secundário curto"},
    ],
    "hashtags": ["#História", "hoje na história", "Titanic", "#genoma"],
    "risk": {"level": "medio", "reasons": ["Tema sensível: mortes em tragédia e atentado."]},
}


def sample() -> Carousel:
    return Carousel.model_validate(SAMPLE)
