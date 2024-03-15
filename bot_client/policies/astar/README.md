```mermaid
flowchart
	n1["Receive Game State"]
	n2["Any Frightened Ghosts?"]
	n3["Move to Nearest Ghost"]
	n4["Dangerous Pellets Collected?"]
	n5["Waiting Next to Superpellet?"]
	n6["Frightened Ghosts Very Close?"]
	n7["Move To Superpellet"]
	n8["Wait for Ghosts"]
	n9["GameMode?"]
	n10["Move to Pellet"]
	n11["Move To Superpellet Waiting Spot"]
	n12["Continue Startup Sequence"]
	n1 --> n2
	n2 -- "Yes" --> n3
	n2 -- "No" --> n4
	n4 -- "Yes" --> n5
	n5 -- "Yes" --> n6
	n6 -- "Yes" --> n7
	n6 -- "No" --> n8
	n5 -- "No" --> n9
	n9 -- "Scatter" --> n10
	n9 -- "Chase" --> n11
	n4 -- "No" --> n12
 ```
