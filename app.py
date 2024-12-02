
import streamlit as st
import string
import nltk
nltk.download('stopwords')
nltk.download('punkt')
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from joblib import load
import sqlite3

ps = PorterStemmer()

def transform_text(text):
    text = text.lower()
    text = nltk.word_tokenize(text)

    y = []
    for i in text:
        if i.isalnum():
            y.append(i)

    text = y[:]
    y.clear()

    for i in text:
        if i not in stopwords.words('english') and i not in string.punctuation:
            y.append(i)

    text = y[:]
    y.clear()

    for i in text:
        y.append(ps.stem(i))

    return " ".join(y)

tfidf = load('vectorizer.pkl')
model = load('model.pkl')

conn = sqlite3.connect('users.db')
c = conn.cursor()

def create_table():
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL
                    )""")

def add_user(username, password):
    hashed_password = password
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
    conn.commit()

def verify_user(username, password):
    c.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    if result:
        hashed_password = result[0]
        return hashed_password == password
    else:
        return False

create_table()

st.title("Spam SMS Detector")

if 'username' not in st.session_state:
    st.session_state.username = None

if st.session_state.username:
    st.write(f"Welcome, {st.session_state.username}!")
    input_sms = st.text_area("Enter the message")
    if st.button('Predict'):
        transformed_sms = transform_text(input_sms)
        vector_input = tfidf.transform([transformed_sms])
        result = model.predict(vector_input)[0]
        if result == 1:
            st.header("Spam")
        else:
            st.header("Not Spam")
else:
    if 'show_register' not in st.session_state:
        st.session_state.show_register = False

    if st.session_state.show_register:
        st.subheader("Register")
        form = st.form(key='register_form')
        register_username = form.text_input('Username')
        register_password = form.text_input('Password', type='password')
        register_submit = form.form_submit_button('Register')
        if register_submit:
            add_user(register_username, register_password)
            st.session_state.show_register = False
            st.session_state.username = register_username
            st.success("Registration successful!")
            st.experimental_rerun()
    else:
        st.subheader("Login")
        form = st.form(key='login_form')
        login_username = form.text_input('Username')
        login_password = form.text_input('Password', type='password')
        login_submit = form.form_submit_button('Login')
        if login_submit:
            if verify_user(login_username, login_password):
                st.session_state.username = login_username
                st.experimental_rerun()
            else:
                st.write('Incorrect username or password')

        st.write("Don't have an account?")
        if st.button('Register'):
            st.session_state.show_register = True
            st.experimental_rerun()

conn.close()
