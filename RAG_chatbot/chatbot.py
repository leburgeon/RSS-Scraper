"""
This script will run a streamlit 'front end' for the RAG chatbot.

When a message is input, streamlit will send a request through AWS API Gateway to a Lambda function,
which will run the RAG pipeline and return a response. The response will then be displayed in the streamlit app.


"""
import streamlit as st

def get_llm_response(user_input:str) -> str:
    """This functions sends the user_input to a backend lambda function via AWS API Gateway,
    and returns the response from the lambda function."""

    




# Set the title of the app
st.title('RAG Chatbot')

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

        get_llm_response(user_input)

        # Add user message to chat history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_input
        })

        bot_response = f'This is a placeholder response to: "{user_input}"'

        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': bot_response
        })

        # Rerun the app to update the chat display
        st.rerun()
    else:
        st.warning('Please enter a question before clicking Send.')









