import React from 'react';

import navcards from '../constants';
import Footer from './Footer';
import Header from './Header';
import Navcards from '../components/navcards/Navcards';


export class Homepage extends React.Component {
    constructor(props) {
        super(props);
    };
    render() {
        return (
            <div>
                <Header pathname='/home' logoImg={this.props.amatLogo}></Header>
                <div className="MainHolder">
                    <div className="MainHolderWrapper">
                        <div className="OnDemandDash">
                            <p>
                                Looking for ON DEMAND Dashboard?
                            </p>
                            <a href="/dashboard">Click here</a>
                        </div>
                        <div className="Big-Logo-Img">
                            <img src={this.props.amatLogo} alt="appliedx"/>
                        </div>
                        <Navcards items={navcards} navcardsImgs={this.props.navcardsImgs}></Navcards>
                    </div>
                </div>
                <Footer/>
            </div>
        );
    }
}
