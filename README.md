# Iterated Prisoner's Dilemma Websocket Server

This repository exists to facilitate hosting a Iterated Prisoner's Dilemma tournament without allowing unvalidated code from running on the organizer's infrastructure.

While other implementations exist, they rely on the organizer running the strategy.

By exposing a websocket based interface, the organizer's exposure is greatly reduced.

One limitation of this approach is that the games are dependent on the participant's input, possibly stalling out a game if one participant does not respond.
To address this, each round has a timeout.
If a participant fails to provide a response within the timeout, their turn is forfeit.

From testing, 200ms a round with 2 python clients appears to be fairly reliable. 
There are some dropouts but its not common.

# References

https://github.com/oldgalileo/bastille

Containerized runners communicating through stdin and stdout. 

https://github.com/Axelrod-Python/Axelrod

Python based prisoner's dilemma tournament w/ metrics.

https://github.com/Mark-MDO47/PrisonDilemmaTourney

Python based prisoner's dilemma tournament
