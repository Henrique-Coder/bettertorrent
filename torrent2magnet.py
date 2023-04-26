from hashlib import sha1
from urllib.parse import urlparse
import streamlit as st
from bencodepy import decode, encode
from requests import get, exceptions


def get_magnet_uri(metainfo):
    info_hash = sha1(encode(metainfo[b'info'])).hexdigest()
    magnet_uri = f'magnet:?xt=urn:btih:{info_hash}'

    return magnet_uri

def get_trackers(metainfo):
    trackers = metainfo[b'announce-list']
    trackers = set(tracker[0].decode() for tracker in trackers)

    return trackers


# Configuracoes da pagina
page_title = 'Arquivo Torrent ➙ URI Magnético'
page_favicon = 'favicon.ico'

st.set_page_config(page_title=page_title, page_icon=page_favicon, layout='centered', initial_sidebar_state='auto')

# Conteudo da pagina
st.title(page_title)
st.write('Faça upload de um arquivo **TORRENT** abaixo para gerar um **URI MAGNÉTICO**.')

uploaded_file = st.file_uploader('Escolha um arquivo **TORRENT**:', type='torrent',
                                 help='O arquivo deve ter a extensão .torrent')

if uploaded_file is not None:
    trackers_count = 0

    metainfo = decode(uploaded_file.read())
    magnet_uri = get_magnet_uri(metainfo)
    magnet_hash = magnet_uri.split(':')[-1]

    warn = st.empty()
    warn.info('Gerando URI magnético...')
    st.markdown('---')

    st.write(f'**URI Magnético ({trackers_count} rastreadores & {len(magnet_uri)} caracteres) ›**')
    st.code(magnet_uri, language='text')
    st.download_button(f'**☁️ Baixar .torrent original ({trackers_count} rastreadores)**', encode(metainfo), f'{magnet_hash}_{trackers_count}-trackers.torrent', 'utf-8')
    st.markdown('---')

    warn.info('Baixando listas de rastreadores para adicionar ao URI Magnético...')

    # Urls das listas de trackers
    trackers_urls = [
        'https://trackerslist.com/all.txt',
        'https://newtrackon.com/api/all',
        'https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all.txt'
    ]

    # Obtém os trackers de cada lista de urls
    trackers = get_trackers(metainfo)

    for url in trackers_urls:
        try:
            resp = get(url)
            resp.raise_for_status()
            resp.encoding = 'utf-8'

            for tracker in resp.text.splitlines():
                if tracker:
                    trackers.add(tracker)

        except exceptions.RequestException:
            pass

    # Adiciona os trackers no uri magnetico
    parsed_magnet_link = urlparse(magnet_uri)
    query_params = parsed_magnet_link.query.split('&')

    for tracker in trackers:
        query_params.append('tr=' + tracker)

    new_query_string = '&'.join(query_params)
    updated_magnet_uri = parsed_magnet_link._replace(query=new_query_string).geturl()

    trackers_count = len(trackers) - 1

    # Atualiza o arquivo torrent para o novo uri magnetico e atualiza o metainfo
    metainfo[b'announce'] = updated_magnet_uri.encode()
    metainfo[b'announce-list'] = [[tracker.encode()] for tracker in trackers]

    st.write(f'**URI Magnético ({trackers_count} rastreadores & {len(updated_magnet_uri)} caracteres) ›**')
    st.code(updated_magnet_uri, language='text')
    st.download_button(f'**☁️ Baixar .torrent atualizado ({trackers_count} rastreadores)**', encode(metainfo), f'{magnet_hash}_{trackers_count}-trackers.torrent', 'utf-8')
    st.markdown('---')

    warn.success('Os rastreadores foram adicionados ao URI Magnético com sucesso!')
