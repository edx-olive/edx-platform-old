import _ from 'lodash';
import qs from 'qs';
import { USER_PROFILE_URL } from './urlPatterns';
import sigV4Client from '../helpers/sigV4Client';


export function ResponseError(message, body) {
    // message: message of the response exception
    // body: object (array) of the error.
    this.message = message
    this.body = body
    this.name = 'ResponseError'
}

function raiseError(e) {
    const message = e.body || 'Oops! Something\'s getting wrong'
    throw new ResponseError(message, e.body)
}

function checkStatus(response) {
    if (response.status >= 200 && response.status < 300) {
        return isJson(response) ?
            response.json()
                .then(json => json, () => response) //return response if no content or can't parse json;
            : response
    } else {
        let error
        if (response.status < 500) {
            error = response.json()
        } else {
            error = response.text()
        }
        return error.then(e => {
            throw new ResponseError(response.statusText, e)
        })
    }
}

const patchAWSSign = (url, awsSettings, params = {}) => {
    params = _.cloneDeep(params);

    const headers = params.headers;
    const body = params.data;
    const method = params.method || 'get';

    if (awsSettings.credentials.accessKeyId) {
        const parsedUrl = new URL(url);
        const path = parsedUrl.pathname;
        const queryParams = qs.parse(parsedUrl.search.substring(1));
        const config = {
            accessKey: awsSettings.credentials.accessKeyId,
            secretKey: awsSettings.credentials.secretAccessKey,
            sessionToken: awsSettings.credentials.sessionToken,
            region: awsSettings.region,
            endpoint: url,
        };
        const signedRequest = sigV4Client.newClient(config).signRequest({
            method,
            path,
            headers,
            queryParams,
            body,
        });
        params.headers = signedRequest.headers;
        url = signedRequest.url;
    } else {
        reloadRequired();
    }
    return { url, params };
}

export const getProfile = (baseUrl, userId, awsSettings) => {
    const fullUrl = baseUrl + USER_PROFILE_URL.replace(/%USER_ID%/g, userId);
    const signedUrl = patchAWSSign(fullUrl, awsSettings);
    let return_data
    // condition for pushed parameters to url in browser
    return_data = fetch(signedUrl.url, signedUrl.params)
        .then(checkStatus)
        .catch(raiseError)
    return return_data
}
