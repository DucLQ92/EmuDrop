from infoscreen import InfoScreen
import check_connection, db_ota
import sys

if __name__ == '__main__':
    infoScreen = InfoScreen()
    connection = check_connection.run(infoScreen=infoScreen)
    if not connection:
        infoScreen.quit()
        sys.exit(1)
        
    # app_ota is deliberately not run: it downloads the upstream release and
    # unpacks it over this directory, which would replace this modified build
    # wholesale. The catalogue below still comes from upstream.
    db_ota.run(infoScreen=infoScreen)
    infoScreen.quit()
    sys.exit(0)