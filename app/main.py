import streamlit as st
import asyncio, urllib3, sys, os
from functions.javadump import do_dump_project

os.environ['LOGLEVEL'] = os.getenv('LOGLEVEL', 'ERROR')

sys.path.insert(0, './functions')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(
    page_title="JAVA DUMPS",
    page_icon="chart_with_upwards_trend",
    layout="wide",
    initial_sidebar_state="auto",
)

 
async def get_data_api():
    styles = {
        "container": {"margin-top": "0px !important", "padding": "0!important", "align-items": "stretch", "background-color": "#fafafa"},
        #"icon": {"color": "black", "font-size": "0px"}, 
        "nav-link": {"font-size": "20px", "text-align": "left", "margin-top":"0px", "--hover-color": "#eee"},
        #"nav-link-selected": {"background-color": "lightblue", "font-size": "20px", "font-weight": "normal", "color": "black"}
        }

    await do_dump_project()

if __name__ == "__main__":
    #main()
    #to perform tests with the python interpreter
    #loop = asyncio.get_event_loop()
    #loop.run_until_complete(obtener_datos_desde_api())

    #for testing with streamlit
    #loop = asyncio.new_event_loop()
    #asyncio.set_event_loop(loop)
    #loop.run_until_complete(obtener_datos_desde_api())
    hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    hide_decoration_bar_style = '''
    <style>
        header {visibility: hidden;}
    </style>
    '''
    st.markdown(hide_decoration_bar_style, unsafe_allow_html=True)

    asyncio.run(get_data_api())