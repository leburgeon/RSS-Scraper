"""
This script will run a streamlit 'front end' for the RAG chatbot.

When a message is input, streamlit will send a request through AWS API Gateway to a Lambda function,
which will run the RAG pipeline and return a response. The response will then be displayed in the streamlit app.


"""
import streamlit as st
import requests


from aws_lambda import send_user_input_to_llm


# Set the title of the app
st.title('Tech Company News Chatbot')

# Initialize chat history in session state if it doesn't exist
# session_state persists data across Streamlit reruns
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Display chat history
for message in st.session_state.chat_history[-4:]:
    if message['role'] == 'user':
        with st.chat_message('user'):
            st.write(message['content'])
    else:
        with st.chat_message('assistant'):
            st.write(message['content'])


user_input = st.text_input(
    label='Type your question here:',
    placeholder='Ask me anything...',
    key='user_input'
)

# Create a Send button
if st.button('Find Answer!'):
    if user_input.strip() != "":

        # Add user message to chat history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_input
        })

        response = requests.post(
            "https://r7dhlutwgk.execute-api.eu-west-2.amazonaws.com/chat",
            params={"question": user_input})

        if response.status_code != 200:
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': "Sorry, there was an error processing your request. Please try again later."
            })
        else:
            bot_response = response.json()

            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': bot_response['response']
            })

        # bot_response = send_user_input_to_llm(user_input)

        # st.session_state.chat_history.append({
        #     'role': 'assistant',
        #     'content': bot_response 
        # })

        # Rerun the app to update the chat display
        st.rerun()
    else:
        st.warning('Please enter a question before clicking Send.')
