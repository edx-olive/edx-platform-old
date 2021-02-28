import React from 'react';
import PropTypes from 'prop-types';
import 'tableau-api';


const TEAM_PATHWAY_PROGRESS_URL = 'https://tableauprd.amat.com/#/site/appliedx/views/WebTesting/TeamsPathwayprogressoverview';


class TeamDashboard extends React.Component {
    componentDidMount() {
        this.initViz();
    }

    initViz() {
        const { userId } = this.props;
        const options = {
            UserId: userId,
            hideTabs: true,
            hideToolbar: true,
            height: '200px',
            width: '100%',
            onFirstInteractive: function () {
                // const iframe = document.getElementsByTagName('iframe')[0];
                // iframe.setAttribute('scrolling', 'no');
                console.log("Run this code when the viz has finished loading.");
            },
        };
        const teamPathwayProgress = this.teamPathwayProgress;
        new window.tableau.Viz(
            teamPathwayProgress,
            TEAM_PATHWAY_PROGRESS_URL,
            options
        );
    }

    render() {
        return (
            <React.Fragment>
                <div
                    className="team-pathway-progress"
                    ref={(ref) => {
                        this.teamPathwayProgress = ref;
                    }}
                ></div>
            </React.Fragment>
        );
    }
}

export default TeamDashboard;


TeamDashboard.propTypes = {
    userId: PropTypes.string.isRequired
};
