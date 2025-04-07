class NextDHCPException(Exception): ...

class InvalidDHCPConfiguration(NextDHCPException):
    """Exception raised for invalid DHCP configuration."""
    pass

class InvalidDatabaseConfiguration(NextDHCPException):
    """Exception raised for invalid database configuration."""
    pass