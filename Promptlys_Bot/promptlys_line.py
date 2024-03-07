import os
import telebot
import hashlib
import json
import openai
from openai import OpenAI
import linebot 

#deprecated!!
##from linebot import LineBotApi
##from linebot import WebhookHandler

from linebot import v3
from linebot import LineBotApi
from linebot.v3.webhook import WebhookHandler
from linebot import LineBotApi
from linebot.models import MessageEvent, TextMessage
from linebot.models import TextSendMessage, ImageSendMessage

# Function to send message to user
def send_message(user_id, message):
    try:
        line_bot_api.push_message(user_id, TextSendMessage(text=message))
    except LineBotApiError as e:
        print(f"Error sending message to user {user_id}: {e}")



### V3 ######
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)
### V3 ######

#from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError
from flask import Flask, request, abort


from telebot import types
from supabase import create_client, Client



openai_key = os.environ['OPENAI_KEY']
supa_url = os.environ['SUPABASE_URL']
supa_key = os.environ['SUPABASE_KEY']
line_access_token = os.environ['LINE_ACCESS_TOKEN']
line_channel_secret = os.environ['LINE_CHANNEL_SECRET']

print("OpenAI KEY IS : ")
print(openai_key)

# Initialize the Supabase client

# Replace with your Supabase service role key
supabase = create_client(supa_url, supa_key)



# Initialize Flask app
app = Flask(__name__)

#unable to use new API format 
try:
    client = OpenAI(api_key = openai_key)
except:
    print("Sorry, OpenAI() failed !!")

# revert to old openai API syntax 
try:
    client.api_key = openai_key
except:
    print("Sorry, No API Key available")



# Initialize Line bot API
line_bot_api = LineBotApi(line_access_token)

### V3 ######
configuration = Configuration(access_token=line_access_token)
### V3 ######

handler = WebhookHandler(line_channel_secret)




# Function to determine user locale based on profile
def get_user_locale(user_id):
    try:
        profile = line_bot_api.get_profile(user_id)
        # Retrieve user profile from Line SDK
        # Access locale information from the user profile
        locale = profile.language 

        # Now you can use the locale information to customize your bot's response
        if locale == 'en':
            print("Locale = ENGLISH !!")
        elif locale == 'ja':
            print("Locale = JAPANESE !!")
        elif locale == 'zh-Hans':
            print("Locale == CHINESE SIMPLIFIED")
        
        else: 
            print("LOCALE == NO LOCALE DEFINED !!")

        return profile.language
    except LineBotApiError as e:
        print(f"Error getting user profile: {e}")
        return None


# Function to get user profile including handle
def get_user_handle(user_id):
    try:
        profile = line_bot_api.get_profile(user_id)
        print("About to get User Display Name")
        return profile.display_name
    except LineBotApiError as e:
        print(f"Error getting user profile: {e}")
        return None



# Function to add or update user info in the "Bot_Accounts" table
def update_bot_accounts(user_id, user_handle, user_locale):

    # Generate a unique referral code using the user's ID
    referral_code = hashlib.sha256(str(user_id).encode('utf-8')).hexdigest()[:10]
    # Check if the user already exists in the database
    print("CHECKING IF USER EXISTS")
    user_exists = supabase.table("Bot_Accounts").select("*").eq("tg_id", user_id).execute()

    # If the user does not exist, insert the new user
    if not user_exists.data:
        supabase.table("Bot_Accounts").insert({
            "tg_id": user_id,
            "tg_handle": user_handle,
            "tg_refcode": referral_code, 
            "tg_type": "Line",
            "tg_locale" : user_locale
           }).execute()
        print("NEW LINE BOT USER INSERTION SUCCESS !!")
    else:
        # Optionally, update the user's handle if it has changed
        supabase.table("Bot_Accounts").update({
            "tg_handle": user_handle,
            "tg_refcode": referral_code,  # Update this if you want to allow referral code updates
            "tg_locale": user_locale
        }).eq("tg_id", user_id).execute()
        print("LINE BOT USER UPDATE SUCCESS !!")
        print("User ID =")
        print(user_id)


# Function to get the count of unique users
def get_unique_user_count():
    result = supabase.table("Bot_Accounts").select("tg_id", count='exact').execute()
    return result.count if result.count is not None else 0

# Function to send message with clickable link 
def send_message_with_link(user_id, message_with_link):
    try:
        # Send a message with a clickable link
        line_bot_api.push_message(
            user_id,
            TextSendMessage(text=message_with_link)
        )
        print("Message sent successfully!")
    except Exception as e:
        print(f"Error sending message: {e}")


# Function to handle incoming messages
def handle_message(event):
    user_id = event.source.user_id
    message_text = event.message.text

    # Determine user's locale
    locale = get_user_locale(user_id)
    #locale = event.source.locale
    
    # Process message based on prefixes
    if message_text.startswith('/about'):
        # Define the about message in English
        about_message_en = (
            "Promptlys is a Professional Prompt network whose mission is to optimize generative AI communications via effective prompting.\n\n"
            "On Promptlys, you can input a general topic and the prompt generator will produce a list of prompts that convert your intentions into relevant, well-constructed prompts.\n\n"
            "On Promptlys, you can search a library of publicly shared prompts by keyword or category, connect with prompt experts, and subscribe to premium prompt experts channels.\n\n"
            "Promptlys is built on a freemium model. With a $100/year subscription you can access premium and customized prompts that can save thousands per month, for hiring a copywriter, graphic designer, or a programmer.\n\n"
            "Please visit us at our website: https://demo.promptlys.ai"
        )
        
        # Define the about message in Traditional Chinese
        about_message_zh = (
            "Promptlys 是一個專業的提示網絡，其使命是通過有效的提示來優化生成式 AI 通信。\n\n"
            "在 Promptlys 上，您可以輸入一般主題，提示生成器將生成一系列提示，將您的意圖轉換為相關的、構建良好的提示。\n\n"
            "在 Promptlys 上，您可以通過關鍵字或類別搜索一個公開共享的提示庫，與提示專家聯繫，訂閱高級提示專家頻道。\n\n"
            "Promptlys 建立在免費模型之上。通過每年 100 美元的訂閱，您可以訪問高級和定制的提示，這可以節省成千上萬美元，用於聘請文案撰寫、平面設計師或程序員。\n\n"
            "請訪問我們的網站: https://demo.promptlys.ai"
        )
        
        # Define the about message in Japanese
        about_message_ja = (
            "Promptlys は、効果的なプロンプトを介して生成 AI コミュニケーションを最適化することを使命とするプロフェッショナル プロンプト ネットワークです。\n\n"
            "Promptlys では、一般的なトピックを入力すると、プロンプト生成器が意図を関連する、よく構築されたプロンプトに変換するリストを生成します。\n\n"
            "Promptlys では、キーワードやカテゴリで共有されたプロンプトのライブラリを検索したり、プロンプト専門家と連絡を取ったり、プレミアム プロンプト専門家のチャンネルに登録したりできます。\n\n"
            "Promptlys はフリーミアム モデルで構築されています。年間 100 ドルの定期購読で、月額数千ドルを節約できるプレミアムおよびカスタマイズされたプロンプトにアクセスできます。\n\n"
            "ウェブサイトをご覧ください: https://demo.promptlys.ai"
        )

        # Determine which message to send based on user's locale
        if locale == 'ja':
            send_message_with_link(user_id, about_message_ja)
        elif locale != 'en':
            send_message_with_link(user_id, about_message_zh)
        else:
            send_message_with_link(user_id, about_message_en)

    elif message_text.startswith('/guide'):
        send_guide_message(user_id, locale)
    elif message_text.startswith('chat:') or message_text.startswith('prompt:') or message_text.startswith('Chat:') or message_text.startswith('Prompt:'):
        print("about to process user input with OpenAI !!!")
        invoke_openai_api(user_id, message_text, locale)
    elif message_text.startswith('/prompt') or message_text.startswith('/chat') or message_text.startswith('/Prompt') or message_text.startswith('/Chat'):
        print("about to process user input with OpenAI !!!")
        invoke_openai_api(user_id, message_text, locale)
    elif message_text.startswith('/image') or message_text.startswith('/Image') :
        print("about to process user image input with OpenAI !!!")
        invoke_openai_api(user_id, message_text, locale)
    #elif message_text.startswith('prompt:'):
        #invoke_openai_api(user_id, message_text[len('prompt:'):], locale)
    else:
        # Default response for unrecognized messages
        # send_default_response(user_id, locale)
        # Prepend 'chat: ' to the message text
        modified_message_text = '/chat ' + message_text
        # Invoke OpenAI API with the modified message text
        print("about to process user input with OpenAI !!!")
        invoke_openai_api(user_id, modified_message_text, locale)

# Function to send guide message
def send_guide_message(user_id, locale='zh-Hant'):
    # English version of the guide message
    print("Printing User Guide Message!! ")
    print("User Locale == ")
    print(locale)

    guide_message_en = (
        "1. Type  '/about' to browse what Promptlys is about and visit its website for more info!! \n\n"
        "2. Prefix '/prompt' to your prompt description and the Bot will revise and enhance your prompt !\n\n"
        "3. Prefix /image to a prompt description then the Bot will generate an image based on your prompt description. \n\n"
        "4. Type away in chat and Promptlys Bot will engage and respond to your questions!! \n\n"
        "5. Type '/guide' to replay Promptlys Bot instructions"
    )
    

    # Traditional Chinese version of the guide message
    guide_message_zh = (
        "1. 輸入 '/about' 來瀏覽 Promptlys 的相關資訊並訪問其網站以獲取更多資訊!!"
        "2. 在您的提示描述前加上 /prompt 前缀，Promptlys 機器人將讓您的提示文字更加具體，並輸出高效、結構良好的提示描述供您使用！\n\n"
        "3. 在提示描述中加上 /image 前綴，Promptlys機器人將根據您的提示描述產生圖片。\n\n"
        "4. 輸入聊天內容和提問，Promptlys 機器人會與您聊天並回答您的問題!! \n\n"
        "5. 輸入 /guide  重播 Promptlys Bot 操作說明。\n"
    )
    
    guide_message_ja = (
        "1. '/about' を入力して Promptlys の概要を閲覧し、ウェブサイトで詳細を確認してください!! \n\n"
        "2. /prompt の接頭辞をプロンプト説明に付けると、ボットがプロンプトを改訂して強化します！\n\n"
        "3. /image の接頭辞をつけたプロンプト説明に対して、ボットがプロンプト説明に基づいて画像を生成します。\n\n"
        "4. 輸入聊天內容和提問，Promptlys 機器人會與您聊天並回答您的問題!! \n\n"
        "5. /guide  チャットして質問してください、ボットが応答します。"
    )

    # Determine which message to send based on user's locale

    if locale == 'ja':
        send_message(user_id, guide_message_ja)
    elif locale != 'en':
        send_message(user_id, guide_message_zh)
    else:
        send_message(user_id, guide_message_en)

# Function to send GREETINGS message
def send_greetings_message(user_id):
    # English version of the guide message
    locale = get_user_locale(user_id)
    handle = get_user_handle(user_id)
    print("Printing User Guide Message!! ")
    print("User Locale == ")
    print(locale)

    greetings_message_en = (
        f"Hi, {handle} \U0001F603 😀👍🎉! Welcome to Promptlys Bot, where you optimize your AI conversations with effective prompts! \n\n"
        "1. Type  '/about' to browse what Promptlys is about and visit its website for more info!! \n\n"
        "2. Prefix '/prompt' to your prompt description and the Bot will revise and enhance your prompt !\n\n"
        "3. Prefix /image to a prompt description then the Bot will generate an image based on your prompt description. \n\n"
        "4. Type away in chat and Promptlys Bot will engage and respond to your questions!! 💬 \n\n"
        "5. Type '/guide' to replay Promptlys Bot instructions"
    )
    

    # Traditional Chinese version of the guide message
    greetings_message_zh = (
        f"您好，{handle} \U0001F603😀👍🎉！歡迎使用 Promptlys Bot，這裡您可以通過有效的提示優化您的 AI 對話！\n\n"
        "1. 輸入 '/about' 來瀏覽 Promptlys 的相關資訊並訪問其網站以獲取更多資訊!!"
        "2. 在您的提示描述前加上 /prompt 前缀，Promptlys 機器人將讓您的提示文字更加具體，並輸出高效、結構良好的提示描述供您使用！\n\n"
        "3. 在提示描述中加上 /image 前綴，Promptlys機器人將根據您的提示描述產生圖片。\n\n"
        "4. 輸入聊天內容和提問，Promptlys 機器人會與您聊天並回答您的問題!! 💬 \n\n"
        "5. 輸入 /guide  重播 Promptlys Bot 操作說明。\n"
    )
    
    greetings_message_ja = (
        f"こんにちは、{handle} さん \U0001F603😀👍🎉 ！Promptlys Bot へようこそ。ここでは、効果的なプロンプトで AI 会話を最適化できます！\n\n"
        "1. '/about' を入力して Promptlys の概要を閲覧し、ウェブサイトで詳細を確認してください!! \n\n"
        "2. /prompt の接頭辞をプロンプト説明に付けると、ボットがプロンプトを改訂して強化します！\n\n"
        "3. /image の接頭辞をつけたプロンプト説明に対して、ボットがプロンプト説明に基づいて画像を生成します!!💬\n\n"
        "4. 輸入聊天內容和提問，Promptlys 機器人會與您聊天並回答您的問題!! \n\n"
        "5. /guide  チャットして質問してください、ボットが応答します。"
    )

    # Determine which message to send based on user's locale

    if locale == 'ja':
        send_message(user_id, greetings_message_ja)
    elif locale != 'en':
        send_message(user_id, greetings_message_zh)
    else:
        send_message(user_id, greetings_message_en)




# Function to invoke OpenAI API
def invoke_openai_api(user_id, user_text, locale):
    # Implement OpenAI API invocation to generate response or prompt
    # Replace this placeholder with actual code to call OpenAI API

    # For demonstration purposes, just echo back the input prompt
    #response = f"Received prompt: {prompt}"

    # Enhanced part to interact with the specified OpenAI model
    messages = []
    prompt = ""

    try:
        if user_text.startswith('/image') or user_text.startswith('/Image'):
            print("about to generate Image!!")
            print("Image Prompt = ")
            print(user_text[len("/img"):])
            img_response = client.images.generate(
            model="dall-e-3",
            prompt=user_text[len("/image"):],
            size="1024x1024",
            quality="standard",
            n=1,
            )
            image_url = img_response.data[0].url
            send_image(user_id, image_url)

            return
        
    except Exception as img_e:
        print(f"Error accessing OpenAI API: {img_e}")
        
        if (locale == 'ja'):
            send_message(user_id, "申し訳ありませんが、その画像リクエストは処理できません。後でもう一度お試しください。")
        elif (locale != 'en'):
            send_message(user_id, "抱歉，我無法處理該圖片請求。 請稍後再試.")
        else:
            send_message(user_id, "Sorry, I couldn't process that image generation request. Please try again later.")
        return

    try:
        if user_text.startswith('prompt:') or user_text.startswith('Prompt:') or user_text.startswith('/prompt') or user_text.startswith('/Prompt') :
            messages = [
                {"role": "system", "content": "You are an expert prompt builder that is proficient at digesting vague, generic descriptions and converting them to specific, well-constructed prompt examples that explicitly declares the appropriate role and tone, and effectively communicates user's intentions and goals. Please generate each response in 200 words or less"},
                {"role": "assistant", "content": "This is Context. "},
                {"role": "user", "content": "This is User's Question"}
            ]
            prompt = user_text[len('prompt:'):]
        
        if user_text.startswith('chat:') or user_text.startswith('Chat:') or user_text.startswith('/chat') or user_text.startswith('/Chat'):
            messages = [
                {"role": "system", "content": "You are an expert prompt interpreter that is adept at understanding imperfect, error-prone user prompts and come up with the most optima, relevant, and engaging responses in 150 words or less."},
                {"role": "assistant", "content": "This is Context. "},
                {"role": "user", "content": "This is User's Question"}
            ]
            prompt = user_text[len('chat:'):]
    
        for item in messages:
            if item["role"] == "user":
                item["content"] = prompt
                
        gpt_response = client.chat.completions.create(model="gpt-4-0125-preview",
        messages=messages)

        # unable to use new OpenAI API format, revert to OLD API format 
        #gpt_response = openai.ChatCompletion.create(
                  #  model="gpt-4-0125-preview",
                   # messages=messages 
        #)
        
        bot_reply = gpt_response.choices[0].message.content
        #bot_reply = gpt_response['choices'][0]['message']['content']

        print("about to Send OPENAI response back!!")
        send_message(user_id, bot_reply)

        return 

    except Exception as e:
        print(f"Error accessing OpenAI API: {e}")
        if (locale == 'ja'):
            send_message(user_id, "申し訳ありませんが、その画像リクエストは処理できません。後でもう一度お試しください。")
        elif (locale != 'en'):
            send_message(user_id, "抱歉，我無法處理該請求。 請稍後再試.")
        else:
            send_message(user_id, "Sorry, I couldn't process that request. Please try again later.")
        return

    if locale == 'ja':
        send_message(user_id, f"あなたのプロンプトの説明を受け取りました：{prompt}")
    
    elif locale != 'en':
        send_message(user_id, f"收到你的提示描述: {prompt}")
        #line_bot_api.push_message(user_id,  f"收到你的提示描述: {prompt}")
    else : 
        send_message(user_id, f"Received your prompt: {prompt}")
        #line_bot_api.push_message(user_id,  f"Received prompt: {prompt}")

# Function to send default response for unrecognized messages
def send_default_response(user_id, locale):
    # Default response for unrecognized messages
    if  locale == 'ja':
        default_response = "申し訳ありませんが、理解できませんでした。Promptlys Bot の操作説明を見るには /guide と入力してください。"
    elif locale != 'en':
        default_response = "抱歉，我沒有理解。請輸入 /guide 查看Promptlys Bot 操作說明。"
    else: 
        default_response = "Sorry, I didn't understand that. Please type '/guide' to view Promptlys Bot instructions."

    send_message(user_id, default_response)

# Function to send message to user
def send_message(user_id, message):
    try:
        line_bot_api.push_message(user_id, TextSendMessage(text=message))
    except LineBotApiError as e:
        print(f"Error sending message to user {user_id}: {e}")

from linebot.models import ImageSendMessage

# Function to send an image message to user
def send_image(user_id, image_url):
    try:
        line_bot_api.push_message(user_id, ImageSendMessage(original_content_url=image_url, preview_image_url=image_url))
    except LineBotApiError as e:
        print(f"Error sending image to user {user_id}: {e}")


# Define webhook endpoint for receiving messages
@app.route('/webhook', methods=['POST'])
def webhook():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    # Parse the JSON body to extract events
    events = json.loads(body)['events']
    print("IN WEBHOOK: ABOUT TO ITERATE THRU EVENTS and LOOK FOR FOLLOW !! ")
    # Iterate through events
    for event in events:
        # Check if the event is a Follow Event
        if event['type'] == 'follow':
            # Extract user ID
            print("IN WEBHOOK: FOLLOW EVENT CAPTURED!!!")
            #user_id = event.source.user_id
            user_id = event['source']['userId']
            
            # Send locale-specific language message
            send_greetings_message(user_id)
    return 'OK'




##### V2 #############

# Register message event handler
## @handler.add(MessageEvent, message=TextMessage)
## def handle_message_event(event):
    # Extract user ID and handle from the event
    ##user_id = event.source.user_id
   ## user_handle = get_user_handle(user_id)  # Assuming sender_id is the handle, adjust accordingly
    
    # Invoke the function to update bot accounts
    ## update_bot_accounts(user_id, user_handle)
    
   ## handle_message(event)




##### V3 ########

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message_event(event):
    try:
        print("event object looks like:")
        print(event)
        print("userID = ")
        print("user_id")
        # Extract user ID and handle from the event
        user_id = event.source.user_id
        user_handle = get_user_handle(user_id)  # Assuming sender_id is the handle, adjust accordingly
        user_locale = get_user_locale(user_id)

        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            message_text = ''
            if user_locale == 'ja':
                message_text = f'ACK: {event.message.text}\n\n 誠に申し訳ございませんが、Promptlys はトラフィックが多いため現在オフラインになっています。できるだけ早くオンラインに戻ります。!!..'
            elif user_locale != 'en':
                message_text = f'ACK: {event.message.text}\n\n 我們致以誠摯的歉意: Promptlys 目前由於流量超過而處於離線狀態，我們將盡快恢復上線！..'
            else:
                message_text = f'ACK: {event.message.text}\n\n Sincere apologies:  Promptlys is currently offline due to high traffic,  we will be back online as soon as we can!!..'

            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=message_text)]  # Prefix added here
                )
            )
        
    

        # Invoke the function to update bot accounts
        update_bot_accounts(user_id, user_handle, user_locale)
        
        print("about to Handle User Message")
        # Handle the message
        handle_message(event)
    except Exception as e:
        print(f"Error handling message: {e}")





if __name__ == '__main__':
    app.run()


#################################################################


































