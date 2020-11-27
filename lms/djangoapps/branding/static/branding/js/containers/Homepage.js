import React from 'react';

import navcards from '../constants';
import Footer from './Footer';
import Header from './Header';
import ManagerDashboard from '../pages/ManagerDashboard';
import Navcards from '../components/navcards/Navcards';
import { UserProfileProvider } from '../context/UserProfile'
import { APIDataProvider } from '../context/APIContext'


export class Homepage extends React.Component {
    constructor(props) {
        super(props);
    };

    render() {

        return (
            <div>
                <APIDataProvider
                  baseAPIUrl={this.props.baseAPIUrl} awsSettings={this.props.awsSettings}
                  userId={this.props.userId} reqHeaders={this.props.reqHeaders}>
                    <UserProfileProvider>
                        <Header pathname='/home' logoImg={this.props.amatLogo}></Header>
                        <div className="MainHolder">
                            <div className="OnDemandDash">
                                <p>Looking for the ON DEMAND Dashboard?</p>
                                <a href="/dashboard">Click here</a>
                            </div>
                            <div className="MainHolderWrapper">
                                <div className="Big-Logo-Img">
                                    <img src={this.props.amatLogo} alt="appliedx"/>
                                </div>
                                <div className="Mainwrapper Mainwrapper_dashboard">
                                    <ManagerDashboard />
                                </div>
                                <Navcards items={navcards} navcardsImgs={this.props.navcardsImgs}></Navcards>
                            </div>
                        </div>
                        <Footer/>
                    </UserProfileProvider>
                </APIDataProvider>
            </div>
        );
    }
}
