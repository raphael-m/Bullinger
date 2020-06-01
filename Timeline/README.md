The tool can be ran successfully if the following instructions are followed:

* Clone the repository:
```
git clone https://github.com/choco-brownies/bullinger_timeline.git
```
* In the bullinger_timeline directory create and activate virtual environment:
```
cd bullinger_timeline
virtualenv -p python3 venv
source venv/bin/activate
```
* Install all dependencies from the file requirements.txt:
```
pip install -r requirements.txt
```

* Start Bullinger Timeline tool:
```
python server.py
```

In the file urls.txt can be found the list of urls that can be used for the timeline.
When the server is started and running, any url from the urls.txt can be put in the browser and the tool which represents timeline of exchanged letters between Heinrich Bullinger and other person will be shown.
Example that shows of exchanged letters between Heinrich Bullinger and Johannes Fabricius can be shown using url:
```
http://0.0.0.0:5000/Fabricius/Johannes
```

Sent and received messages are represented in different colours. Red coloured flags are representing messages sent by Bullinger and green coloured flags are representing messages Bullinger received.

Please do not click on it very fast on zoom buttons of the timeline. After click, please wait for a moment so the timeline is fully refreshed and zoomed.
