from hashlib import sha1
from urllib.parse import urlparse
from webbrowser import open

import streamlit as st
from bencodepy import decode, encode
from requests import get, exceptions


page_title = 'Arquivo Torrent ➙ URI Magnético'
page_favicon = 'favicon.ico'

st.set_page_config(page_title=page_title, page_icon=page_favicon, layout='centered', initial_sidebar_state='auto')


def get_magnet_link(metainfo):
    info = metainfo[b'info']
    info_bencoded = encode(info)
    info_hash = sha1(info_bencoded).hexdigest()
    magnet_uri = f'magnet:?xt=urn:btih:{info_hash}'
    return magnet_uri

def get_trackers(metainfo):
    trackers = metainfo[b'announce-list']
    trackers = set(tracker[0].decode() for tracker in trackers)
    return trackers


st.title(page_title)

st.write('Faça upload de um arquivo .torrent abaixo para gerar um link magnético.')

uploaded_file = st.file_uploader('Escolha um arquivo .torrent', type='torrent',
                                 help='O arquivo deve ter a extensão .torrent')

if uploaded_file is not None:
    metainfo = decode(uploaded_file.read())
    magnet_uri = get_magnet_link(metainfo)

    warn = st.empty()
    warn.info('Gerando URI magnético...')

    st.markdown('---')

    st.write('**URI Magnético sem rastreadores**')
    st.code(magnet_uri, language='text')

    warn.info('Baixando listas de rastreadores para adicionar ao URI magnético...')

    # URLs das listas de trackers
    trackers_urls = [
        'https://newtrackon.com/api/all',
        'https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all.txt',
        'https://raw.githubusercontent.com/XIU2/TrackersListCollection/master/all.txt'
    ]

    # Obtém os trackers do arquivo torrent
    trackers = get_trackers(metainfo)

    # Obtém os trackers de cada lista de URLs
    for url in trackers_urls:
        try:
            response = get(url)
            response.raise_for_status()
            response.encoding = 'utf-8'
            for tracker in response.text.splitlines():
                if tracker:
                    trackers.add(tracker)
        except exceptions.RequestException:
            pass

    # Adiciona os trackers no link magnético
    parsed_magnet_link = urlparse(magnet_uri)
    query_params = parsed_magnet_link.query.split('&')
    for tracker in trackers:
        query_params.append('tr=' + tracker)
    new_query_string = '&'.join(query_params)
    updated_magnet_uri = parsed_magnet_link._replace(query=new_query_string).geturl()

    trackers_count = len(trackers) - 1

    st.write(f'**URI Magnético com {trackers_count} rastreadores**')
    st.code(updated_magnet_uri, language='text')

    st.markdown('---')

    col1_1, col1_2, col1_3, col1_4 = st.columns(4)

    col1_2.button('Abrir URI Magnético Original', on_click=lambda: open(magnet_uri, new=2))
    col1_3.button('Abrir URI Magnético com Rastreadores', on_click=lambda: open(updated_magnet_uri, new=2))

    warn.success('Os rastradores foram adicionados ao URI magnético com sucesso!')
