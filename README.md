# GateOverflow-WebTool


Requirements

    flask
    flask_cors
    subprocess
    requests
    bs4
    re
    pandas

1. Open the terminal and paste the below commands(you must have install git in your machine)

       git clone https://github.com/NME-rahul/GateOverflow-WebTool.git

2. nevigate to directory GateOverflow-WebTool

       cd GateOverflow-WebTool

3. make sure you have python and pip intall in you machine

       pip install --upgrade pip
       pip install -r requirements.txt

4. run the flask server on your local machine

       python flask_server.py [port]

5. open the `Web_interface.html` file on the localhost http://localhost:[port]/api (find this line and paste as shown below in image).
6. If anyone wants to run the same in local network then run the `Web_interface.html` file on the speicfied private IP by the tool(you will see this in your terminal).
<p text-align="center"> <img width="479" alt="Screenshot 2025-05-31 at 2 39 05 PM" src="https://github.com/user-attachments/assets/bc69476c-9151-4f3d-8ffb-52df7faba31c" /></p>


---

to run scraper.py independetly

    python scraper.py --tags [tags] --limit [limit]


> limit sepcifies the nuber of page you want to scrap, for each page you'll get 20 questions.
