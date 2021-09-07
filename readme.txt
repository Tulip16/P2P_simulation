1. Run the following command for compiling and running our simulator:
	python3 simulator.py

2. After running input the following parameters to the simulator in command line:
	a. simulation time in milli seconds
	b. number of peers
	c. percentage of fast peers (e.g. input 60 for percentage of fast peers to be 60%)
	d. Tx(mean inter-transaction gap) in milli seconds
	e. Tk(mean POW time) for peer k = 1 in milli seconds
	f. Tk(mean POW time) for peer k = 2 in milli seconds
	g. Tk(mean POW time) for peer k = 3 in milli seconds
	h. Tk(mean POW time) for peer k = 4 in milli seconds

3. It will prompt you about if you want to track txn generation, loopless forwarding and latencies
	input Y for yes
	input N for no

4. It will prompt you about if you want to track blk creation, broadcast, verification, fork resolution
	input Y for yes
	input N for no

5. For every peer, it will prompt you about if you want to view the blockchain tree for the peer
	input Y for yes
	input N for no

	Then it will prompt you about if you want to view the blockchain tree in compressed format
		input Y for yes
		input N for no

6. To generate Figure 1 and Figure 2 in Part 8 of the report, run the following command:
	python3 plot1.py

7. To generate Figure 3 in Part 8 of the report, run the following command:
	python3 plot2.py