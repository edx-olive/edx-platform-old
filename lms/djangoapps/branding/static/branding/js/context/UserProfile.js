import React from 'react';
import PropTypes from 'prop-types';
import { getProfile } from '../api/profile';
import { APIDataContext } from './APIContext';


export const UserProfileContext = React.createContext()

export class UserProfileProvider extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            didMount: false,
            isLoading: false,
            profile: null
        };
    }

    async componentDidMount() {
        this.setState({'isLoading': true, didMount: true});

        let profile = await getProfile(
          this.context.baseUrl, this.context.userId,
          this.context.awsSettings, this.context.reqHeaders
        ) || {};
        profile = profile ? profile.data : {};
        const imgData = profile.profileImage;
        if (imgData) {
            profile.imageSrc = 'data:image/png;base64,' + imgData;
        }

        this.setState({
            isLoading: false,
            profile: Object.assign({}, profile),
        });
    }

    render() {
        if (!this.state.didMount) return null;
        return (
            <UserProfileContext.Provider value={Object.assign({}, this.state)}>
                {this.props.children}
            </UserProfileContext.Provider>
        );
    }
}

UserProfileProvider.contextType = APIDataContext;

UserProfileProvider.propTypes = {
    children: PropTypes.node.isRequired,
};
