import streamlit as st
import openai
import pandas as pd
import yaml
import json

run_on_cloud = True

csv_file = 'Taigi_translation_template.csv'
download_file = 'Taigi_translation_test_download.csv'
prompt_template_file = 'prompt_template_example.txt'
output_format_example_file = 'output_format_example.json'
function_call_for_ChatGPT = 'function_call_for_ChatGPT.json'

#@st.cache_data
def get_df():
    #read in the csv file, if not exist create one
    try:
        df = pd.read_csv( csv_file, engine='pyarrow')
    except:
        df = pd.DataFrame(columns=['Taigi_sentence', 'English_translation','Alt_English_translation','Tokenized_Taigi', 'Tokenized_English', 'Japanese_translation', 'Notes'], dtype = 'string')
    
    #add an empty row to the dataframe
    #df.loc[len(df.index)] = ['','','','','','','']

    return df

#
#
#

st.set_page_config('Taigi-English Translation Copilot',layout="wide")

######### sidebar buttons ########
st.sidebar.header('Management area')

#ask for OpenAI API key

openai_api_key = st.sidebar.text_input('OpenAI API Key', value='', key='chatbot_api_key')

st.sidebar.markdown('''Get OpenAI access key here : [OpenAI API](https://openai.com/blog/openai-api)''')

#create a checkbox to use/not use example
#use_example = st.sidebar.checkbox('Use output data format example', value = False, key = 'use_example') 
use_example = False
#
#
#

def ask_LLM(prompt_list, functions, function_call ):

    if openai_api_key != '':

        if functions == {} or function_call == 'none':

            response = openai.ChatCompletion.create(model="gpt-3.5-turbo-0613", messages = prompt_list)

        else:
            response = openai.ChatCompletion.create(model="gpt-3.5-turbo-0613", messages = prompt_list, functions = [functions], function_call = "auto")
        
        msg = response.choices[0].message

    else:
    
        msg = {"role": "assistant", 
               "content": 'Please add your OpenAI API key to continue.',
               "function" : {} }
        
    print(msg)

    print('----- the above is funciton call response----')
    
    return msg


def get_translation( prompt_template, functions, function_call ):

    prompt_list = {"role": "assistant", "content": prompt_template },
    
    if function_call != 'none':
        print( prompt_list )
        print( functions )

    msg = ask_LLM(prompt_list, functions, function_call )

    # Step 2, check if the model wants to call a function
    if msg.get("function_call"):
        function_name = msg["function_call"]["name"]

    #print msg in utf-8
    #print( msg.get("content") )
    
    #if msg.get("function_call"):
    #    print('funciton call by ChatGPT : ', msg["function_call"]["name"])

    print(msg)

    return msg

#@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')

# persist state of dataframe
# session_state = SessionState.get(df=data)
if 'df' not in st.session_state:
    st.session_state.df = get_df()
if 'Taigi_sentence' not in st.session_state:
    st.session_state.Taigi_sentence = ''     
if 'Tokenized_Taigi_done' not in st.session_state:
    st.session_state.Tokenized_Taigi_done = '' 
if 'Tokenized_English_done' not in st.session_state:
    st.session_state.Tokenized_English_done = ''
if 'English_done' not in st.session_state:
    st.session_state.English_translation_done = ''
if 'Alternative_English_done' not in st.session_state:
    st.session_state.Alt_English_translation_done = ''   
if 'Japanese_done' not in st.session_state:
    st.session_state.Japanese_translation_done = ''
if 'Notes' not in st.session_state:
    st.session_state.Notes_done = ''

if 'result_df' not in st.session_state:
    #create a dataframe to store the result, columns = 'Taigi_sentence','Tokenized_Taigi','Tokenized_English','English_translation','Alt_English_translation','Japanese_translation','Notes'
    st.session_state.result_df = pd.DataFrame(columns = ['Taigi_sentence','Tokenized_Taigi','Tokenized_English','English_translation','Alt_English_translation','Japanese_translation','Notes'], dtype = 'string')
    
if 'st.session_state.prompt_template_dict' not in st.session_state:
    with open( prompt_template_file, 'r') as f:
        st.session_state.prompt_template_dict = yaml.load(f, Loader=yaml.FullLoader)  
# data format example
if 'st.session_state.example_dict' not in st.session_state:
    #load from json file, file_path = output_format_example_file
    st.session_state.example_dict = json.load(open(output_format_example_file, 'r'))
# function call interface for ChatGPT
if 'st.session_state.function_call_for_ChatGPT' not in st.session_state:
    #load from json file, file_path = function_call_for_ChatGPT
    st.session_state.function_call_for_ChatGPT = json.load(open(function_call_for_ChatGPT, 'r'))
                                              
def clear_all_result():

    st.session_state.Taigi_sentence = '' 
    st.session_state.Tokenized_Taigi_done = '' 
    st.session_state.Tokenized_English_done = ''
    st.session_state.English_translation_done = ''
    st.session_state.Alt_English_translation_done = ''
    st.session_state.Japanese_translation_done = ''
    st.session_state.Notes_done = ''

    #also clear prompot template edit
    #with open('prompt_template_example.yaml', 'r') as f:
    #    st.session_state.prompt_template_dict = yaml.load(f, Loader=yaml.FullLoader)  

    Taigi_sentence_input = ''
    Tokenized_Taigi_input = ''
    Tokenized_English_input = ''
    English_translation_input = ''
    Alt_English_translation_input = ''
    Japanese_translation_input = ''
    Notes_input = ''
    Freely_use_input = ''

    #clear result df
    st.session_state.result_df = pd.DataFrame(columns = ['Taigi_sentence','Tokenized_Taigi','Tokenized_English','English_translation','Alt_English_translation','Japanese_translation','Notes'], dtype = 'string')

    return


#create a checkbox button to disable/enable an input area

#create a checkbox button to disable/enable an input area
prompt_template_edit = st.sidebar.checkbox('Edit prompt template', value = False, key = 'prompt_template_edit')

# Option to show Chinese dictionary reference expander
Chinese_dict_reference = st.sidebar.checkbox('Optinal Chinese translation reference', value = False, key = 'Chinese_dict_reference')

#vreate a slider to select number od sentences to generate
sentence_count = st.sidebar.slider('Number of sentences to generate', 1, 10, 1, key = 'slider_01' )
                  
#st.sidebar.write('')
#if st.sidebar.button('Show function calls', key = 'show_function_calls'):
#    st.sidebar.write( st.session_state.function_call_for_ChatGPT )

#create a button to show result
if st.sidebar.button('Show result'):
    st.sidebar.write( st.session_state.result_df.to_dict('index')[0] )

#create a button to clear all result
clear_all = st.sidebar.button('Clear all result', on_click=clear_all_result, key = 'clear_all' )

if clear_all:
    st.sidebar.write('All result cleared')

st.sidebar.write('')

if run_on_cloud == False:
    #create a button to save the dataframe as csv to local
    if st.sidebar.button('Save csv to local'):
        st.session_state.df.to_csv(csv_file, index=False)
        st.sidebar.write('csv saved to local')

#create a button to download the dataframe
    csv = convert_df(st.session_state.df)

    st.sidebar.download_button(
        label="Download dataframe as CSV",
        data=csv,
        file_name=download_file,
        mime='text/csv',
    )

######################
##### main page ######
######################
# there are 7 containers
# for Tokenized_Taigi -00
# for Tokenized_English -01
# for English_translation -02
# for Alt_English_translation -03
# for Japanese_translation  -04
# for Notes -05
# for Freely_use to inquire LLM anything -06

st.header('Taigi-English Translation Copilot')
#st.write('This app uses OpenAI\'s API to assit translating Taig to English. Please enter a sentence in Taigi and the follow the pipeline.')

st.write()

###################################################
##### Stage 00 : Taigi_sentence to Tokenized_Taigi
###################################################
# create an expander
with st.expander('Pipeline stage 00 - Tokenize Taigi', expanded = True):

    if use_example:
        use_example_00 = st.checkbox('Use data format example for this stage', value = False, key = 'use_example_00')
        if use_example_00:
            example_00 = st.session_state.example_dict['Tokenized_Taigi']['prefix'] + str(st.session_state.example_dict['Tokenized_Taigi']['format'])
        else:
            example_00 = ''    
    else:
        example_00 = ''

    #create a checkbox to use/not use function to hint ChatGPT
    #use_function_00 = st.checkbox('Use function for ChatGPT to call', value = False, key = 'use_function_00') 
    
    #if use_function_00:

    #    functions = st.session_state.function_call_for_ChatGPT['Tokenized_Taigi']['function']
    #    function_call = 'auto'

    #else:
        #functions = {}
        #function_call = 'none'

    # Translation pipeline stage 00 : tokenize the sentence in CJK word, annotating the part of speech
    prompt_template_to_Tokenize_Taigi = st.text_area('Prompt to Tokenize Taigi sentence (editable)', value = st.session_state.prompt_template_dict['prompt_template_to_Tokenize_Taigi'], disabled = not prompt_template_edit )
    #if prompt_template_to_Tokenize_Taigi:
    st.session_state.prompt_template_dict['prompt_template_to_Tokenize_Taigi'] = prompt_template_to_Tokenize_Taigi

    #input box for Taigi sentence to be tokenized and translated
    Taigi_sentence_input = st.text_area('Tokenize the Taigi sentence and annotating POS', st.session_state.Taigi_sentence, key = '00')

    prompt = prompt_template_to_Tokenize_Taigi.replace('[[[number]]]', str(sentence_count)).replace('[[[example]]]', example_00 ) + Taigi_sentence_input

    if Taigi_sentence_input != '':

        st.session_state.Taigi_sentence = Taigi_sentence_input

        st.write( f'Final prompt to LLM : ' + prompt )
        #st.write( f'Function call : {function_call}' )
        #st.write( f'Function list : {functions}' )

        if st.button('Generate Tokenized Taigi',key='submit_00') and Taigi_sentence_input != '':

            response = get_translation( prompt, functions = {}, function_call = 'none' )

            st.write()
            st.write('[ Stage 00 ] : Convert Taigi_sentence to Tokenized_Taigi ->\n ')
            st.write(response.get('content'))

            #if response.get("function_call"):
            #   function_name = response["function_call"]["name"]
                    # Note: the JSON response from the model may not be valid JSON
                #function_response = function_name_specified(
                #arg1=message.get("arg1"),
                #arg2=message.get("arg2"),

            st.write('Result also sent to the next stage for chek and edit.')
            st.session_state.Tokenized_Taigi_done = response['content']

    else:
        st.session_state.Taigi_sentence = ''
        st.write('Please ake sure to input a Taigi sentence to start with.')


###################################################
##### Stage 00-1 : Reference Chinese dictionary, result of this stage only for reference and will not be saves as result
###################################################
# Translation pipeline stage 00-1 : Reference Chinese dictionary, only modificaion of prompt_template saved and can be downloaded.  
if Chinese_dict_reference == True:

    # create an expander
    with st.expander('(Optional) Pipeline stage 01_1 - Reference Chinese dictionary, result will not be saved as result', expanded = True):
    
        if use_example:
            use_example_00_1 = st.checkbox('Use data format example for this stage', value = False, key = 'use_example_00_1')
            if use_example_00_1:
                example_00_1 = st.session_state.example_dict['Chinese_translation']['prefix'] + str(st.session_state.example_dict['Chinese_translation']['format'])
            else:
                example_00_1 = ''    
        else:
            example_00_1 = ''

        prompt_template_to_ref_Chinese_dict = st.text_area('Prompt to Tokenize Taigi sentence (editable)', value = st.session_state.prompt_template_dict['prompt_template_to_ref_Chinese_dict'], disabled = not prompt_template_edit )
    
        if prompt_template_to_ref_Chinese_dict:
            st.session_state.prompt_template_dict['prompt_template_to_ref_Chinese_dict'] = prompt_template_to_ref_Chinese_dict

        #input box for Tokenized Taigi
        ref_Chinese_dict_input = st.text_area('Get Chinese-English word translation for reference', st.session_state.Tokenized_Taigi_done, key = '00_1' )

        #st.session_state.Tokenized_Taigi_done = Tokenized_Taigi_input

        if ref_Chinese_dict_input != '':

            prompt = prompt_template_to_ref_Chinese_dict.replace('[[[number]]]', str(sentence_count)).replace('[[[example]]]',  example_00_1 ) + ref_Chinese_dict_input

            st.write( 'Final prompt to LLM : \n' + prompt )

            if st.button('Get reference from Chinese dictionary',key='submit_00_1') and ref_Chinese_dict_input != '':

                prompt, response = get_translation( prompt)

                st.write()
                st.write('[ Optional : Stage 00_1 ] : Get reference of Tokenized Taigi words from Chinese-English dictionaly ->\n', response)
                st.write('Result only for reference here and will not be saved as result.')
                #st.session_state.ref_Chinese_dict_done = response

        else:
            st.write('Please run previous stages first or make sure to input someting by your self.')


###################################################
##### Stage 01 : Tokenized_Taigi to Tokenized_English
###################################################
# Translation pipeline stage 01 : translating Tokenized Taigi into Tokenized English, annotating the part of speech by prompt
# create an expander
with st.expander('Pipeline stage 01 - Tokenize English', expanded = True):

    if use_example:
        use_example_01 = st.checkbox('Use data format example for this stage', value = False, key = 'use_example_01')
        if use_example_01:
            example_01 = st.session_state.example_dict['Tokenized_English']['prefix'] + str(st.session_state.example_dict['Tokenized_English']['format'])
        else:
            example_01 = ''    
    else:
        example_01 = ''

    prompt_template_to_Tokenize_English = st.text_area('Prompt to Tokenize Taigi sentence (editable)', value = st.session_state.prompt_template_dict['prompt_template_to_Tokenize_English'], disabled = not prompt_template_edit )
    
    if prompt_template_to_Tokenize_English:
        st.session_state.prompt_template_dict['prompt_template_to_Tokenize_English'] = prompt_template_to_Tokenize_English

    #input box for Tokenized Taigi
    Tokenized_Taigi_input = st.text_area('Convert Tokenized Taigi word list into Tokenized English word list', st.session_state.Tokenized_Taigi_done, key = '01' )

    if Tokenized_Taigi_input:
        st.session_state.Tokenized_Taigi_done = Tokenized_Taigi_input

    #st.session_state.Tokenized_Taigi_done = Tokenized_Taigi_input

    if Tokenized_Taigi_input != '':

        prompt = prompt_template_to_Tokenize_English.replace('[[[number]]]', str(sentence_count)).replace('[[[example]]]', example_01 ) + Tokenized_Taigi_input

        st.write( 'Final prompt to LLM : \n' + prompt )

        if st.button('Generate Tokenized English',key='submit_01') and Tokenized_Taigi_input != '':

            prompt, response = get_translation( prompt)

            st.write()
            st.write('[ Stage 01 ] : Tokenized Taigi to Tokenized_English ->\n', response)
            st.write('Result also sent to the next stage for chek and edit.')
            st.session_state.Tokenized_English_done = response

    else:
        st.write('Please run previous stages first or make sure to input someting by your self.')

###################################################
### Stage 02 : Tokenized_English to English
###################################################
# create an expander
with st.expander('Pipeline stage 02 - English translation', expanded = True):
    # Translation pipeline stage 02 : converting Tokenized English into English

    if use_example:
        use_example_02 = st.checkbox('Use data format example for this stage', value = False, key = 'use_example_02')
        if use_example_02:
            example_02 = st.session_state.example_dict['English_translation']['prefix'] + str(st.session_state.example_dict['English_translation']['format'])
        else:
            example_02 = ''    
    else:
        example_02 = ''

    prompt_template_to_English = st.text_area('Prompt to generate English sentence from Tokenize English (editable)', value = st.session_state.prompt_template_dict['prompt_template_to_English'], disabled = not prompt_template_edit )
    if prompt_template_to_English:
        st.session_state.prompt_template_dict['prompt_template_to_English'] = prompt_template_to_English

    #input box for English translation
    English_translation_input = st.text_area('Convert Tokenized English words lists into English', st.session_state.Tokenized_English_done, key = '02' )

    if English_translation_input:
        st.session_state.English_translation_done = English_translation_input

    if English_translation_input != '':

        prompt = prompt_template_to_English.replace('[[[number]]]', str(sentence_count)).replace('[[[example]]]', example_02 ) + English_translation_input

        st.write( 'Final rompt to LLM : \n' + prompt )

        if st.button('Generate English',key='submit_02') and English_translation_input != '':

            prompt, response = get_translation( prompt )

            st.write()
            st.write('[ Stage 02 ] : Convert Tokenized English word lists to English translations ->\n', response)
            st.write('Result also sent to the next stage for chek and edit.')
            st.session_state.English_translation_done = response

    else:
        st.write('Please run previous stages first or make sure to input someting by your self.')

###################################################
### Stage 03 : English to alternative English
###################################################
# create an expander
with st.expander('Pipeline stage 03 - Generate alternative English translation', expanded = True):

    if use_example:
        use_example_03 = st.checkbox('Use data format example for this stage', value = False, key = 'use_example_03')
        if use_example_03:
            example_03 = st.session_state.example_dict['Alt_English_translation']['prefix'] + str(st.session_state.example_dict['Alt_English_translation']['format'])
        else:
            example_03 = ''    
    else:
        example_03 = ''

    # Translation pipeline stage 03 : generating alternative English sentences

    prompt_template_to_alt_English = st.text_area('Prompt to generate more alternatives English sentence from previous English translations (editable)', value = st.session_state.prompt_template_dict['prompt_template_to_alt_English'], disabled = not prompt_template_edit )
    if prompt_template_to_alt_English:
        st.session_state.prompt_template_dict['prompt_template_to_alt_English'] = prompt_template_to_alt_English

    #input box for alternative English translation
    Alt_English_translation_input = st.text_area('generating alternative English translations from previous English translations', st.session_state.English_translation_done, key = '03' )

    if Alt_English_translation_input:
        st.session_state.Alt_English_translation_done = Alt_English_translation_input

    if Alt_English_translation_input != '':

        prompt = prompt_template_to_alt_English.replace('[[[number]]]', example_03) + Alt_English_translation_input

        st.write( 'Final prompt to LLM : \n' + prompt )

        if st.button('Generate Alternative English translations',key='submit_03') and Alt_English_translation_input != '':

            prompt, response = get_translation( prompt )

            st.write()
            st.write('[ Stage 03 ] : Generating alternative English sentenves from previous English translations ->\n', response)
            st.write('Result also sent to the next stage for chek and edit.')
            st.session_state.Alt_English_translation_done = response

    else:
        st.write('Please run previous stages first or make sure to input someting by your self.')
        
###################################################
### Stage 04 : English and alternative English to Japanese
###################################################
# create an expander
with st.expander('Pipeline stage 04 - Expand it if you want to generate Japanese translations', expanded = False):

    if use_example:
        use_example_04 = st.checkbox('Use data format example for this stage', value = False, key = 'use_example_04')
        if use_example_04:
            example_04 = st.session_state.example_dict['Japanese_translation']['prefix'] + str(st.session_state.example_dict['Japanese_translation']['format'])
        else:
            example_04 = ''    
    else:
        example_04 = ''  

    # Translation pipeline stage 04 : generating alternative English sentences

    prompt_template_to_Japanese = st.text_area('Prompt to generate Japanese translations from previous English translations (editable)', value = st.session_state.prompt_template_dict['prompt_template_to_Japanese'], disabled = not prompt_template_edit )

    if prompt_template_to_Japanese:
        st.session_state.prompt_template_dict['prompt_template_to_Japanese'] = prompt_template_to_Japanese

    #input box for Japanese translation
    Japanese_translation_input = st.text_area('generating Japanese translations from previous English translations', st.session_state.Alt_English_translation_done, key = '04' )

    if Japanese_translation_input:
        st.session_state.Japanese_translation_done = Japanese_translation_input

    if Japanese_translation_input != '':

        prompt = prompt_template_to_Japanese.replace('[[[number]]]', str(sentence_count)).replace('[[[example]]]',  example_04)  + Japanese_translation_input

        st.write( 'Final prompt to LLM : \n' + prompt )

        if st.button('Generate Japanese teanslation',key='submit_04') and Japanese_translation_input != '':

            prompt, response = get_translation( prompt )

            st.write()
            st.write('[ Stage 04 ] : Generating Japanese translations from previous English translations ->\n', response)
            st.write('Pipeline finished, you may put notes or check and save result.')
            st.session_state.Japanese_translation_done = response

        #show the Japanese translation in the text box
        Japanese_translation_edit = st.text_area('Japanese translation', st.session_state.Japanese_translation_done, key = '04_1' )

        if st.button('Check then confirm Japanese translation modification',key='submit_04_2'):
            st.session_state.Japanese_translation_done = Japanese_translation_edit
            st.write('Japanese translation confirmed -> ', st.session_state.Japanese_translation_done)

    else:
        st.write('Please run previous stages first or make sure to input someting by your self.')

###################################################
### Stage 05 : Notes area
###################################################
# create an expander
with st.expander('Pipeline stage 05 - Expand it if you need to put notes', expanded = False):
    
    st.divider()
    st.write('Area for you to append notes to the translations, not part of translation pipeline')
    # Translation pipeline stage 05 : generating alternative English sentences

    Notes_input = st.text_area('Area for you to put notes','', key = '05' )
    if Notes_input != '':

        if st.button('Submit notes',key='submit_05'):
            st.session_state.Notes_done = Notes_input
            st.write('Notes submitted -> ', st.session_state.Notes_done)
            st.write('Please check final result, append it to the dataframe, and then save.')

###################################################
### Stage 06 : Not part of translation pipeline, double check the final translation and save/manage result
###################################################
# create an expander
with st.expander('Pipeline stage 06 - Double check and manage result', expanded = True):
    
    st.divider()
    st.write('Final check and modification, not part of translation pipeline')

    #edit the dataframe
    st.write('Final translation result for you to check and edit')

    #add one row to the dataframe
    st.session_state.result_df.loc[0] = [
                st.session_state.Taigi_sentence,
                st.session_state.Tokenized_Taigi_done,
                st.session_state.Tokenized_English_done,
                st.session_state.English_translation_done,
                st.session_state.Alt_English_translation_done,
                st.session_state.Japanese_translation_done,
                st.session_state.Notes_done ]

    st.data_editor( st.session_state.result_df , key="result_editor") 

    #create a button to add result to df
    if st.button('Append result to df and clear all'):
        st.session_state.df = pd.concat([st.session_state.df, st.session_state.result_df], ignore_index=True)

        #clear result_df
    
        clear_all_result()
        st.write('Result append to dataframe and all result cleared')
        st.write('Dataframe affter append: ', st.session_state.df)

col1, col2, col3 = st.columns(3)

with col1:
    #create a button to show the entire df
    display_df = st.button('Show the entire dawtaframe', key = 'display_df')

with col2:
    #create a button to delete the last row row
    if st.button('Delete the last row'):
        # delete last row
        if len(st.session_state.df) > 0:
            st.session_state.df = st.session_state.df.tail(-1)
        else:
            st.write('Dataframe empty')
with col3:
    st.write('')    

#show the entire df
if display_df:
    st.write(st.session_state.df)
################################################
#### end of the translation pipeline ####
################################################

# part of sidebar


dict_to_save = {'prompt_template_to_Tokenize_Taigi': prompt_template_to_Tokenize_Taigi, 
                'prompt_template_to_Tokenize_English': prompt_template_to_Tokenize_English, 
                'prompt_template_to_English': prompt_template_to_English, 
                'prompt_template_to_alt_English': prompt_template_to_alt_English, 
                'prompt_template_to_Japanese': prompt_template_to_Japanese, 
                    }

if run_on_cloud == False:
#create a radio button to dicide show or save the prompt_template YAML to local
    prompt_template_handle = st.sidebar.radio('Show/Save prompt_template to local', ('Show', 'Save', 'Download'), index = 0)
    actions = 'Show/Save'
else:
    prompt_template_handle = 'Show'
    actions = 'Show'

    #create a button to save the prompt_template YAML to local

if st.sidebar.button(f'{actions} prompt_template'):

    if prompt_template_handle == 'Show':
        st.sidebar.write(dict_to_save)

    elif prompt_template_handle == 'Save':

        with open('/home/martin/TG/Taigi_parse/prompt_template_example.yaml', 'w') as f:
            yaml.dump( dict_to_save, f, allow_unicode=True)
        
        st.sidebar.write('prompt_template saved to local')

        #convert dic_to_save to a text string, changeline = '\n'

def dict_to_text(dict_to_save):
        
    text_contents = ''

    for key, value in dict_to_save.items():
        text_contents += f'{key} : \'{value}\'\n'

    return text_contents
    
text_contents = dict_to_text(dict_to_save)

download_prompt_template = st.sidebar.download_button(
        label="Download prompt_template as \'your_prompt_template.txt\'",
        data=text_contents,
        file_name='your_prompt_template.txt',
        mime='text/csv',
                ) 
if download_prompt_template:
    st.sidebar.write('prompt_template downloaded')




