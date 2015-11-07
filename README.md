I am assuming that each client knows only about the proxy it needs to talk to when it wants to reach the server. Each client only has one proxy available to it. This should be sufficient because the proxies share data

How do we want to represent the data in the server?
	* A dictionary with a set of keys. The client can request a list of all the keys, and then request that key

How do we want to store data in the proxy?
	* A dictionary with a set of keys, and each element has a TTL, which is refreshed. 



