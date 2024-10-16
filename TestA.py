import streamlit as st
import firebase_admin
import requests
from firebase_admin import credentials, auth, firestore
import os

# Ottieni le credenziali di Firebase dall'ambiente
firebase_credentials = os.getenv('FIREBASE_CREDENTIALS')
cred = credentials.Certificate(eval(firebase_credentials))

# Inizializza Firebase solo se non è già stato fatto
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()  # Inizializza Firestore

FIREBASE_API_KEY = os.getenv('FIREBASE_API_KEY')

# Inizializza Firestore
db = firestore.client()

# Funzione per autenticare l'utente con email e password tramite la REST API di Firebase
def authenticate_user(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    response = requests.post(url, json=payload)
    return response.json()


# Funzione per inviare una email di recupero password
def send_password_reset(email):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_API_KEY}"
    payload = {
        "requestType": "PASSWORD_RESET",
        "email": email
    }
    response = requests.post(url, json=payload)
    result = response.json()
    if 'error' in result:
        return {"error": result['error']['message']}
    return result


def app():
    # Finestra laterale
    st.sidebar.title("Menu")

    # Pulsante "HOME"
    if st.sidebar.button("HOME"):
        st.session_state.page = "home"

    # Pulsante "Sei un giocatore?"
    if st.sidebar.button("Sei un giocatore?"):
        st.session_state.page = "login_signup"

    # Pagina principale
    if st.session_state.get('page', 'home') == "home":
        st.title('Modigliana Calcio')
        st.markdown('Applicazione in cantiere!')
        st.markdown('Questa è la pagina principale. Puoi navigare per accedere o registrarti.')

    # Sezione di login/signup/recupero password
    elif st.session_state.page == "login_signup":
        st.title('Modigliana Calcio')
        selezione = st.selectbox('Login/Signup', ['Login', 'Sign Up', 'Recupera password'])

        # Sezione Login
        if selezione == 'Login':
            st.markdown('## Sei già registrato?')
            email = st.text_input('Indirizzo Email')
            password = st.text_input('Password', type='password')
            if st.button('Login'):
                response = authenticate_user(email, password)
                if 'idToken' in response:
                    st.session_state.user_email = email  # Salva l'email dell'utente
                    st.success(f'Benvenuto, {email}!')
                    st.markdown(
                        """
                        <div style="position: fixed; bottom: 170px; left: 50%; transform: translateX(-50%); background-color: #90EE90; color: black; padding: 10px 20px; border-radius: 5px; text-align: center;">
                        🎉 Hooray! Good job, but now double click
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    st.write("<div style='height: 50px;'></div>", unsafe_allow_html=True)
                    st.session_state.page = "user_profile"  # Passa alla pagina del profilo
                else:
                    st.warning('Credenziali errate. Riprova.')

        # Sezione Sign Up
        elif selezione == 'Sign Up':
            st.markdown('### Registrati qui')
            email = st.text_input('Indirizzo Email (Registrazione)')
            password = st.text_input('Password (Registrazione)', type='password')
            if st.button('Crea Account'):
                try:
                    # Crea un nuovo utente con email e password
                    user = auth.create_user(email=email, password=password)
                    st.success('Account creato con successo!')
                    st.markdown(
                        """
                        <div style="position: fixed; bottom: 170px; left: 50%; transform: translateX(-50%); background-color: #90EE90; color: black; padding: 10px 20px; border-radius: 5px; text-align: center;">
                        🎉 Hooray! Good job, but now double click
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    st.write("<div style='height: 50px;'></div>", unsafe_allow_html=True)
                    st.session_state.user_email = email  # Salva l'email dell'utente
                    
                    # Reindirizza alla pagina per inserire informazioni aggiuntive
                    st.session_state.page = "complete_profile"  # Cambia pagina a "complete_profile"
                except Exception as e:
                    st.warning('Creazione account fallita. Riprova.')  # Messaggio generico

        # Sezione Recupera password
        elif selezione == 'Recupera password':
            st.markdown('## Recupera la tua password')
            reset_email = st.text_input('Inserisci il tuo indirizzo email per il recupero')
            if st.button('Invia Richiesta di Recupero'):
                response = send_password_reset(reset_email)
                if 'error' not in response:
                    st.success('Email di recupero inviata con successo! Controlla la tua casella email.')
                else:
                    st.warning('Invio della richiesta di recupero fallito. Riprova.')  # Messaggio generico

    # Nuova pagina per completare il profilo utente
    elif st.session_state.page == "complete_profile":
        st.title('Completa il tuo Profilo')
        st.markdown('### Inserisci le tue informazioni personali')
        last_name = st.text_input('Cognome')
        first_name = st.text_input('Nome')
        gender = st.radio('Genere', ['Maschio', 'Femmina'])
        date_of_birth = st.text_input("Nato il (DD-MM-YYYY)", value="01-01-2000")
        birthplace = st.text_input('Luogo di Nascita').lower().capitalize()
        indirizzo = st.text_input('Residenza in via')
        civico = st.text_input('Civico')
        comune = st.text_input('Comune')
        
        if st.button('Salva Informazioni'):
            # Verifica che tutti i campi siano compilati e non siano None
            if None in [first_name, last_name, date_of_birth, birthplace, indirizzo, civico, comune] or \
                    '' in [first_name, last_name, date_of_birth, birthplace, indirizzo, civico, comune]:
                st.warning("Tutti i campi devono essere compilati e non possono essere vuoti!")
            else:
                # Salva le informazioni nel Firestore come stringa
                db.collection('users').document(st.session_state.user_email).set({
                    'first_name': first_name,
                    'last_name': last_name,
                    'date_of_birth': date_of_birth,  # Salva come stringa
                    'gender': gender,
                    'birthplace': birthplace,
                    'indirizzo': indirizzo,
                    'civico': civico,
                    'comune': comune
                })
                st.success('Informazioni salvate con successo!')
                st.session_state.page = "user_profile"  # Cambia pagina al profilo utente

    # Nuova pagina per il profilo utente
    elif st.session_state.page == "user_profile":
        st.title('Profilo Utente')
        st.markdown('Ecco le tue informazioni.')

        # Recupera i dati dell'utente da Firestore
        user_doc = db.collection('users').document(st.session_state.user_email).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            first_name = st.text_input('Nome', value=user_data.get('first_name'), key='first_name')
            last_name = st.text_input('Cognome', value=user_data.get('last_name'), key='last_name')
            birthplace = st.text_input('Luogo di Nascita:', value=user_data.get('birthplace'), key='birthplace').lower().capitalize()
            # Mostra la data di nascita come stringa
            date_of_birth = user_data.get('date_of_birth') if user_data.get('date_of_birth') else "01-01-2000"
            date_of_birth_input = st.text_input("Nato il (DD-MM-YYYY)", value=date_of_birth).lower().capitalize()

            opzioni_genere = ['Maschio', 'Femmina']
            genere_predefinito = user_data.get('gender')
            index_predefinito = opzioni_genere.index(genere_predefinito) if genere_predefinito in opzioni_genere else 0
            gender = st.radio('Genere', opzioni_genere, index=index_predefinito, key='gender')
            indirizzo = st.text_input('Residenza in via', value=user_data.get('indirizzo'), key='indirizzo').lower().capitalize()
            civico = st.text_input('Civico', value=user_data.get('civico'), key='civico').lower().capitalize()
            comune = st.text_input('Comune', value=user_data.get('comune'), key='comune').lower().capitalize()
            
            if st.button('Aggiorna Informazioni'):
                # Verifica che tutti i campi siano compilati e non siano None
                if None in [first_name, last_name, date_of_birth_input, birthplace, indirizzo, civico, comune] or \
                        '' in [first_name, last_name, date_of_birth_input, birthplace, indirizzo, civico, comune]:
                    st.warning("Tutti i campi devono essere compilati e non possono essere vuoti!")
                else:
                    # Aggiorna i dati nel Firestore
                    db.collection('users').document(st.session_state.user_email).update({
                        'first_name': first_name,
                        'last_name': last_name,
                        'gender': gender,
                        'date_of_birth': date_of_birth_input,
                        'birthplace': birthplace,
                        'indirizzo': indirizzo,
                        'civico': civico,
                        'comune': comune
                    })
                    st.success('Informazioni aggiornate con successo!')
        else:
            st.warning('Nessuna informazione trovata.')  # Messaggio generico


# Avvia l'app
if __name__ == '__main__':
    app()
