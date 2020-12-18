import React from 'react';
import PropTypes from 'prop-types';
import { getManagerTeam } from '../api/team';
import { APIDataContext } from './APIContext';


export const TeamContext = React.createContext()

export class TeamProvider extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            didMount: false,
            isLoading: false,
            team: null,
        };
    }

    async componentDidMount() {
        this.setState({'isLoading': true, didMount: true});

        let team = await getManagerTeam(
          this.context.baseUrl, this.context.userId,
          this.context.awsSettings, this.context.reqHeaders
        ) || {};

        this.setState({
            isLoading: false,
            team: Object.assign({}, team),
        });
    }

    render() {
        if (!this.state.didMount) return null;
        return (
            <TeamContext.Provider value={Object.assign({}, this.state)}>
                {this.props.children}
            </TeamContext.Provider>
        );
    }
}

TeamProvider.contextType = APIDataContext;

TeamProvider.propTypes = {
    children: PropTypes.node.isRequired,
};
