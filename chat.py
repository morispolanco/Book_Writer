import re
import openai
from time import time, sleep
from halo import Halo
import textwrap
import yaml


###     file operations


def save_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)

def append_file(filepath, content):
    with open(filepath, 'a', encoding='utf-8') as outfile:
        outfile.write(content)


def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as infile:
        return infile.read()


###     API functions


def chatbot(conversation, model="gpt-4-0613", temperature=0, max_tokens=2000):
    max_retry = 7
    retry = 0
    while True:
        try:
            spinner = Halo(text='Thinking...', spinner='dots')
            spinner.start()
            
            response = openai.ChatCompletion.create(model=model, messages=conversation, temperature=temperature, max_tokens=max_tokens)
            text = response['choices'][0]['message']['content']

            spinner.stop()
            
            return text, response['usage']['total_tokens']
        except Exception as oops:
            print(f'\n\nError communicating with OpenAI: "{oops}"')
            exit(5)


def chat_print(text):
    formatted_lines = [textwrap.fill(line, width=120, initial_indent='    ', subsequent_indent='    ') for line in text.split('\n')]
    formatted_text = '\n'.join(formatted_lines)
    print('\n\n\nCHATBOT:\n\n%s' % formatted_text)


if __name__ == '__main__':
    openai.api_key = open_file('key_openai.txt').strip()
    
    conversation = list()
    conversation.append({'role': 'system', 'content': open_file('system_01_intake.md')})
    user_messages = list()
    all_messages = list()
    chat_print('Describe your requirement to the intake bot. Type DONE when done.')
    
    ## INTAKE PORTION
    
    while True:
        # get user input
        text = input('\n\nUSER: ').strip()
        if text == 'DONE':
            break
        user_messages.append(text)
        all_messages.append('USER: %s' % text)
        conversation.append({'role': 'user', 'content': text})
        response, tokens = chatbot(conversation)
        conversation.append({'role': 'assistant', 'content': response})
        all_messages.append('INTAKE: %s' % response)
        chat_print('\n\nINTAKE: %s' % response)
    
    ## CHARTING NOTES
    chat_print('\n\nGenerating Intake Notes')
    conversation = list()
    conversation.append({'role': 'system', 'content': open_file('system_02_prepare_notes.md')})
    text_block = '\n\n'.join(all_messages)
    chat_log = '<<BEGIN INTAKE CHAT>>\n\n%s\n\n<<END USER INTAKE CHAT>>' % text_block
    save_file('logs/log_%s_chat.txt' % time(), chat_log)
    conversation.append({'role': 'user', 'content': chat_log})
    notes, tokens = chatbot(conversation)
    chat_print('\n\nNotes version of conversation:\n\n%s' % notes)
    save_file('logs/log_%s_notes.txt' % time(), notes)
    
    ## GENERATING outline
    bookName = 'logs/log_%s_book.txt' % time()
    chat_print('\n\nGenerating Outline Report')
    conversation = list()
    conversation.append({'role': 'system', 'content': open_file('system_03_outline_write.md')})
    conversation.append({'role': 'user', 'content': notes})
    report, tokens = chatbot(conversation)
    save_file(bookName, report)
    chat_print('\n\nOutline Report:\n\n%s' % report)

    ## Explain Outline

    chat_print('\n\nExplain Outline')
    conversation = list()
    conversation.append({'role': 'system', 'content': open_file('system_04_outline_explain.md')})
    conversation.append({'role': 'user', 'content': report})
    outline, tokens = chatbot(conversation)
    save_file('logs/log_%s_outline.txt' % time(), outline)
    chat_print('\n\nExplain Outline:\n\n%s' % outline)

    ## Write every chapter
    chat_print('\n\nWrite every chapter')
    conversation = list()
    conversation.append({'role': 'system', 'content': open_file('system_05_detail_write.md')})
    conversation.append({'role': 'user', 'content': notes})
    for line in outline.split('\n'):
        conversation.append({'role': 'user', 'content': line})
        details, tokens = chatbot(conversation)
        append_file(bookName, details)
        chat_print('\n\nWrite every chapter:\n\n%s' % details)
