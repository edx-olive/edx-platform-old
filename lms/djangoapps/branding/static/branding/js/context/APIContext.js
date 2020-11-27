import React from 'react';
import PropTypes from 'prop-types';


export const APIDataContext = React.createContext()

export class APIDataProvider extends React.Component {
    constructor(props) {
        super(props);
    };

    render() {
        const apiContext = {
            baseUrl: this.props.baseAPIUrl,
            awsSettings: this.props.awsSettings,
            userId: this.props.userId,
            reqHeaders: this.props.reqHeaders
        };
        return (
            <APIDataContext.Provider value={apiContext}>
                {this.props.children}
            </APIDataContext.Provider>
        );
    }
}

APIDataProvider.propTypes = {
    children: PropTypes.node.isRequired,
};
