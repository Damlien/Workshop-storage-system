import streamlit as st
import time
# Vi importerer funksjonene fra "hjernen" din
from inventory_service import get_inventory, new_item, search_item, change_stock, update_item

# --- OPPSETT AV SIDEN ---
st.set_page_config(layout="wide", page_title="Lagerstyring System")

# --- SESSION STATE (Hukommelsen til appen) ---
# Vi må huske disse tingene mellom hvert klikk
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "selected_item_id" not in st.session_state:
    st.session_state.selected_item_id = None
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "details" # Kan være "details" eller "new_item"

# ==========================================
# DEL 1: LOGIN SKJERM (Erstatter show_login_screen)
# ==========================================
if not st.session_state.logged_in:
    st.title("🔐 Logg inn")
    
    col1, col2 = st.columns(2)
    
    # 1. Vanlig bruker login
    with col1:
        st.subheader("Butikkmedarbeider")
        if st.button("Logg inn som Medarbeider"):
            st.session_state.logged_in = True
            st.session_state.is_admin = False
            st.rerun()

    # 2. Admin login
    with col2:
        st.subheader("Administrator")
        password = st.text_input("Passord", type="password")
        if st.button("Logg inn som Admin"):
            if password == "1234": # Samme passord som i Tkinter
                st.session_state.logged_in = True
                st.session_state.is_admin = True
                st.rerun()
            else:
                st.error("Feil passord!")
    
    st.stop() # Stopper koden her så ingen ser resten før de er logget inn

# ==========================================
# DEL 2: HOVEDAPP (Når man er logget inn)
# ==========================================

# Toppmeny
col_header, col_logout = st.columns([8, 1])
role_name = "ADMINISTRATOR" if st.session_state.is_admin else "Butikkmedarbeider"
col_header.title(f"📦 Lagerstyring - {role_name}")

if col_logout.button("Logg ut"):
    st.session_state.logged_in = False
    st.session_state.selected_item_id = None
    st.rerun()

st.divider()

# SPLIT VIEW: Vi lager to kolonner (Venstre: Liste, Høyre: Detaljer)
left_col, right_col = st.columns([1, 1]) # 50/50 fordeling

# --- VENSTRE SIDE (SØK OG LISTE) ---
with left_col:
    st.subheader("Søk i lageret")
    search_query = st.text_input("Skriv inn navn...", placeholder="Søk...")
    
    # Hent data
    if search_query:
        inventory_data = search_item(search_query)
    else:
        inventory_data = get_inventory()

    # Vis listen. Vi bruker knapper for å velge vare (siden Streamlit tabeller er statiske)
    st.write(f"Fant {len(inventory_data)} varer:")
    
    # Header for listen
    c1, c2, c3, c4 = st.columns([1, 3, 1, 1])
    c1.markdown("**ID**")
    c2.markdown("**Navn**")
    c3.markdown("**Antall**")
    c4.markdown("**Velg**")
    
    for item in inventory_data:
        rc1, rc2, rc3, rc4 = st.columns([1, 3, 1, 1])
        rc1.write(str(item['id']))
        rc2.write(item['name'])
        rc3.write(str(item['quantity']))
        
        # Velg-knapp
        if rc4.button("👉", key=f"sel_{item['id']}"):
            st.session_state.selected_item_id = item['id']
            st.session_state.view_mode = "details"
            st.rerun()

    # ADMIN: Knapp for ny vare
    if st.session_state.is_admin:
        st.write("---")
        if st.button("➕ Registrer ny vare", type="primary"):
            st.session_state.view_mode = "new_item"
            st.session_state.selected_item_id = None
            st.rerun()
    else:
        st.info("Logg inn som admin for å registrere nye varer.")

# --- HØYRE SIDE (DETALJER OG HANDLINGER) ---
with right_col:
    st.container(border=True) # Lager en ramme rundt høyre side
    
    # MODUS 1: REGISTRER NY VARE (Kun Admin)
    if st.session_state.view_mode == "new_item" and st.session_state.is_admin:
        st.subheader("Ny Vare Registrering")
        
        with st.form("new_item_form"):
            new_name = st.text_input("Navn")
            new_id = st.number_input("ID (Tall)", step=1, min_value=1)
            new_qty = st.number_input("Startantall", step=1, min_value=0)
            new_shelf = st.text_input("Hylleplass")
            
            submitted = st.form_submit_button("Lagre Vare")
            if submitted:
                try:
                    new_item(new_name, int(new_id), int(new_qty), new_shelf)
                    st.success("Vare opprettet!")
                    st.session_state.view_mode = "details"
                    time.sleep(1) # Vent litt så brukeren ser meldingen
                    st.rerun()
                except Exception as e:
                    st.error(f"Feil: {e}")
        
        if st.button("Avbryt"):
            st.session_state.view_mode = "details"
            st.rerun()

    # MODUS 2: VIS DETALJER (Hvis en vare er valgt)
    elif st.session_state.selected_item_id is not None:
        # Finn varen basert på ID
        current_item = next((item for item in get_inventory() if item["id"] == st.session_state.selected_item_id), None)
        
        if current_item:
            st.subheader(f"Detaljer for: {current_item['name']}")
            
            # --- STOCK KONTROLL (For alle brukere) ---
            st.markdown("### Lagerstatus")
            stock_col1, stock_col2, stock_col3 = st.columns([1, 2, 1])
            
            with stock_col1:
                if st.button("➖", key="big_minus", use_container_width=True):
                    change_stock(current_item['id'], -1)
                    st.rerun()
            
            with stock_col2:
                # Viser tallet stort og sentrert
                st.markdown(f"<h1 style='text-align: center; margin: 0;'>{current_item['quantity']}</h1>", unsafe_allow_html=True)
            
            with stock_col3:
                if st.button("➕", key="big_plus", use_container_width=True):
                    change_stock(current_item['id'], 1)
                    st.rerun()
            
            # Manuelt uttak/innskudd
            st.write("") # Mellomrom
            man_col1, man_col2, man_col3 = st.columns([2, 1, 1])
            amount = man_col1.number_input("Manuelt antall", min_value=1, value=5, label_visibility="collapsed")
            if man_col2.button("Ta ut"):
                change_stock(current_item['id'], -amount)
                st.rerun()
            if man_col3.button("Fyll på"):
                change_stock(current_item['id'], amount)
                st.rerun()

            st.divider()

            # --- REDIGERING (Kun Admin) ---
            if st.session_state.is_admin:
                st.markdown("### Rediger Vare (Admin)")
                
                # Vi bruker current_item sine verdier som default
                edit_name = st.text_input("Navn", value=current_item['name'])
                edit_id = st.text_input("ID", value=str(current_item['id']))
                edit_shelf = st.text_input("Hylle", value=current_item.get('shelf', ''))
                
                if st.button("Lagre Endringer", type="primary"):
                    try:
                        update_item(
                            old_id=current_item['id'],
                            new_id=int(edit_id),
                            new_name=edit_name,
                            new_quantity=current_item['quantity'], # Vi endrer ikke antall her
                            new_shelf=edit_shelf
                        )
                        st.success("Endringer lagret!")
                        # Oppdater ID i session state hvis den ble endret
                        st.session_state.selected_item_id = int(edit_id)
                        time.sleep(1)
                        st.rerun()
                    except ValueError:
                        st.error("ID må være et tall")
            
            # --- INFO FOR VANLIGE BRUKERE ---
            else:
                st.markdown("### Info")
                st.write(f"**ID:** {current_item['id']}")
                st.write(f"**Hylleplass:** {current_item.get('shelf', '-')}")
                st.info("Kontakt admin for å endre navn eller ID.")

        else:
            st.error("Fant ikke varen. Kanskje den ble slettet?")
            
    # MODUS 3: INGEN VARE VALGT
    else:
        st.info("👈 Velg en vare fra listen til venstre for å se detaljer.")