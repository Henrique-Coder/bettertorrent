import streamlit as st
from hashlib import sha1
from urllib.parse import urlparse
from bencodepy import decode, encode
from requests import get, exceptions
from random import uniform


class TrackerList:
    def __init__(self):
        tmp_param = str(uniform(0.0000000000000000, 9.9999999999999999))
        self.source_urls = [
            f'https://raw.githubusercontent.com/Henrique-Coder/besttrackers/main/best.txt?tmp={tmp_param}',
        ]


def main_app():
    # Page settings
    page_title = 'Torrent File ⇄ Magnetic URI'
    page_favicon = 'favicon.ico'

    st.set_page_config(
        page_title=page_title,
        page_icon=page_favicon,
        layout='centered',
        initial_sidebar_state='auto',
    )

    # Title and input for mgnetic links
    st.title(page_title)

    magnet_uris_input = st.text_area(
        'Paste your magnetic links here (one per line) ↴',
        height=105,
        help='⬐ You can paste unlimited magnetic links at once.',
    )

    if magnet_uris_input:
        magnet_uris = magnet_uris_input.splitlines()
        magnet_uris = [uri.strip() for uri in magnet_uris if uri.strip()]

        for magnet_uri in magnet_uris:
            parsed_magnet_link = urlparse(magnet_uri)
            query_params = parsed_magnet_link.query.split('&')

            # Get trackers from the input URI
            trackers = set()
            for param in query_params:
                if param.startswith('tr='):
                    trackers.add(param[3:])
            # Get trackers from external lists
            merge_trackers(trackers, TrackerList().source_urls)

            # Add trackers to the URI
            query_params = [
                param for param in query_params if not param.startswith('tr=')
            ]
            for tracker in trackers:
                query_params.append('tr=' + tracker)
            new_query_string = '&'.join(query_params)
            updated_magnet_uri = parsed_magnet_link._replace(
                query=new_query_string
            ).geturl()

            # Display the updated URI with trackers
            st.write('')
            st.write(
                f'SHA1: ***{sha1(updated_magnet_uri.encode()).hexdigest().lower()}* ・** Total of ***{len(trackers) - 1}*** trackers and ***{len(updated_magnet_uri)}*** characters ↴'
            )
            st.code(updated_magnet_uri, language='text')
    st.markdown('---')
    st.write('')
    uploaded_file = st.file_uploader(
        'Select the desired .torrent file (one at a time) ↴',
        type='torrent',
        help='⬐ You can only select one .torrent file at a time.',
    )

    if uploaded_file is not None:
        metainfo = decode(uploaded_file.read())
        magnet_uri = get_magnet_uri(metainfo)
        magnet_hash = magnet_uri.split(':')[-1]

        st.markdown('')

        # Get trackers from each list of urls
        trackers = get_trackers(metainfo)

        merge_trackers(trackers, TrackerList().source_urls)

        # Add trackers to magnetic uri
        parsed_magnet_link = urlparse(magnet_uri)
        query_params = parsed_magnet_link.query.split('&')

        for tracker in trackers:
            query_params.append('tr=' + tracker)
        new_query_string = '&'.join(query_params)
        updated_magnet_uri = parsed_magnet_link._replace(
            query=new_query_string
        ).geturl()

        trackers_count = len(trackers) - 1

        # Update the torrent file to the new magnetic uri and update the metainfo
        metainfo[b'announce'] = updated_magnet_uri.encode()
        metainfo[b'announce-list'] = [[tracker.encode()] for tracker in trackers]

        st.write(
            f'SHA1: ***{sha1(updated_magnet_uri.encode()).hexdigest().lower()}* ・** Total of ***{len(trackers) - 1}*** trackers and ***{len(updated_magnet_uri)}*** characters ↴'
        )
        st.code(updated_magnet_uri, language='text')

        # Download buttons for the torrent file
        scl1, scl2, scl3 = st.columns(3)
        with scl1:
            if st.button(
                    f'Update trackers and reapply them to the **.torrent** file',
                    help='This button will update the trackers and reapply them to the .torrent file.',
            ):
                st.experimental_rerun()
        with scl2:
            st.download_button(
                f'*Download **.torrent** with {trackers_count} trackers*',
                encode(metainfo),
                f'{magnet_hash.lower()}_{trackers_count}-trackers.torrent',
                'utf-8',
                help='This button will download the .torrent file with the updated trackers.',
            )
        with scl3:
            st.download_button(
                '*Download **.txt** with all trackers*',
                '\n'.join(trackers),
                f'{magnet_hash.lower()}_{trackers_count}-trackers.txt',
                'utf-8',
                help='This button will download a .txt file with all the trackers in this torrent (one per line).',
            )


def get_magnet_uri(metainfo):
    info_hash = sha1(encode(metainfo[b'info'])).hexdigest()
    magnet_uri = f'magnet:?xt=urn:btih:{info_hash}'
    return magnet_uri


def get_trackers(metainfo):
    trackers = metainfo[b'announce-list']
    trackers = set(tracker[0].decode() for tracker in trackers)
    return trackers


def merge_trackers(trackers, urls):
    for url in urls:
        try:
            resp = get(url)
            resp.raise_for_status()
            resp.encoding = 'utf-8'
            for tracker in resp.text.splitlines():
                if tracker:
                    trackers.add(tracker)
        except exceptions.RequestException:
            pass


if __name__ == '__main__':
    main_app()
