import React from 'react';

import TeamDashboard from '../components/team/TeamDashboard';
import { UserProfileContext } from '../context/UserProfile';


const ManagerDashboard = () => {
    return <UserProfileContext.Consumer>
        {({profile}) => {
                return (
                  <React.Fragment>
                    {(profile && profile.userId && profile.isManager) &&
                    <div className="ManagerDashboard-Wrapper">
                        <div className="ManagerDashboard-Heading">
                            <h2 className="ManagerDashboard-Title">PATHWAY TEAMS OVERVIEW</h2>
                        </div>
                        <TeamDashboard userId={profile.userId} />
                        <div className="ManagerDashboardLinkHolder">
                            <a href="http://courses/manager/" className="ManagerDashboardLink">Go to Manager Dashboard</a>
                        </div>
                    </div>}
                  </React.Fragment>
                );
        }
      }
    </UserProfileContext.Consumer>;
};


export default ManagerDashboard;
