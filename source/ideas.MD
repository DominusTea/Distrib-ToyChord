- LOGIN Aftereffect:
  local server somehow knows adjacent nodes (ips+ports) / ids
  possibly also return my id

- LOGOUT aftereffect:
  adjacent nodes are updated so they point to correct nodes
  + data rearrangement


- Replication:  
  Each node must know the number of replicas after itself. Aftereffected by lgin /logout ofc.
