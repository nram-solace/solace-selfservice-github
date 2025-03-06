# Github actions POC

Tools for provisioning and managing Solace infrastructure with [Github Actions](https://docs.github.com/en/actions) workflow. 


## Options supported 
- Create multiple queues and auto create JNDI Mapping
- Create multiple client usernames with associated ACL and Client profiles.

### Not supported
- All objects other than Queues, JNDI Mapping, Client username, ACL and Client Profile
- Update properties (eg: update queue spool size)
- Delete objects (eg: delete a client username)