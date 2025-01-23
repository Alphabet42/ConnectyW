1. Create an .env file and copy the text below. Please create the .env file in the src directory. 

TOKEN=""
OWNER_ID=""

The TOKEN is the token id of your bot. You can find it by going to the developer portal -> bot -> token. The owner id is the discord id of the person who is in charge of controlling and managing the network chat. 

2. Install the necessary packages. Make sure you are now in the ConnectyW directory. First, make sure you have pip installed. Once that is done, input the folliwng command to install the  required packages. 

** Windows Uers**
py -m pip install -r requirements.txt

3. Now be back in the src directory. Run the following command.

python main.py 

4. To shut down the program, use the / command feature in discord and select "/shutdown" to end the program. All current data will be saved.

For windows uers, line 262 in the main.py file is required. You can remove this for linux users. My only request is that the bot have a picture of Ryo from Bocchi The Rock. Do leave notes for bugs for I may if I feel like it (likely not). 
