import { raiseError, checkStatus, patchAWSSign } from '../api/index';
import { MANAGER_TEAM_URL } from './urlPatterns';


/**
 * Fetch team data for a given manager.
 *
 * Fetch notifications.
 */
export const getManagerTeam = async (baseUrl, managerId, awsSettings, headers) => {
    const endpointUrl = managerId ? MANAGER_TEAM_URL.replace(/%USER_ID%/g, managerId) : MANAGER_TEAM_URL;
    const fullUrl = baseUrl + endpointUrl;
    let url
    let params = {}

    if ( awsSettings.credentials.secretAccessKey )  {
        const signedUrl = patchAWSSign(fullUrl, awsSettings)
        url = signedUrl.url
        params = signedUrl.params
    } else {
        url = fullUrl
        params.headers = headers
    }
    const response = await fetch(url, params).then(checkStatus).catch(raiseError)

    let { teamName, teamList } = response.data;
    teamList = teamList.map((member) => Object.assign(
      {},
      member,
      {teamCount: parseInt(member.teamCount)},
      {profileImage: 'data:image/png;base64,' + member.profileImage}))

    return {
        teamName,
        teamList
    };
}
