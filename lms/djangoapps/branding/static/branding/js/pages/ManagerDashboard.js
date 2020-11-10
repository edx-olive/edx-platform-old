import React from 'react';

import TeamDashboard from '../components/team/TeamDashboard';
import { UserProfileContext } from '../context/UserProfile';


const ManagerDashboard = () => {
    return <UserProfileContext.Consumer>
        {({profile}) => {
            if (profile && profile.isManager) {
                return (
                    <div className="Mainwrapper ManagerDashboard">
                        <div className="ManagerDashboard-Wrapper">
                            <div className="TeamDashboard-Wrapper">
                                <div className="ManagerDashboard-Heading">
                                    <h2 className="NavCardsListItemTitle">PATHWAY TEAMS OVERVIEW</h2>
                                </div>
                                <TeamDashboard userId={profile.userId} />
                                <div className="NavCardsListItemLinkHolder wide">
                                    <a href="http://courses/manager/v2" className="NavCardsListItemLink">Go to Manager Dashboard</a>
                                </div>
                            </div>
                        </div>
                    </div>
                );
            }
        }}
    </UserProfileContext.Consumer>;
};


export default ManagerDashboard;
