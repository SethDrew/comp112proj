bloom filter (check whether url is present in someone else's cache). 

	- 10 second advertisement window

I am assuming that each client knows which proxy it needs to talk to when it wants to reach the server.

How do we want to represent the data in the server?
	- A dictionary with a set of keys. The client can request a list of all the keys, and then request that key

How do we want to store data in the proxy?
	- A dictionary with a set of keys, and each element has a TTL, which is refreshed. 

How do we want to let proxies talk to eachother?
	- Incoming proxy connections talk on different ports than .



