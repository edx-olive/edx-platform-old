import React, {Component} from 'react';


const avatarImg = "https://s3-us-west-2.amazonaws.com/pathway-frontend-assets/placeholder.png";
const defaultArgs = {'target': '_blank', rel: 'noopener noreferrer', className: 'User-Link'};

const LINKS = [
    {
        name: 'My role (Edit roles)',
        url: 'http://myrole',
        external: true,
        args: defaultArgs
    },
    {
        name: 'Help desk',
        url: 'https://amat.service-now.com/help?id=help_kb_article&sys_id=08d4292ddb442f44df64dd90cf9619b7',
        external: true,
        args: defaultArgs,
        extraItem: <p className="User-Text"><a className="User-Link" href="#footer">About appliedx</a></p>
    },
];


class UserPanel extends Component {

    constructor(props) {
        super(props);

        this.state = {
            userActive: false,
        };

        this.toggleActive = this.toggleActive.bind(this);
        this.closeUserPanel = this.closeUserPanel.bind(this);
    }

    toggleActive(e) {
        e.preventDefault();
        this.setState({
            userActive: !this.state.userActive,
        }, () => {
            document.addEventListener('click', this.closeUserPanel);
        });
    }

    closeUserPanel(e) {
        if (!this.userPanel.contains(e.target)) {
            this.setState({userActive: false}, () => {
                document.removeEventListener('click', this.closeUserPanel);
            });
        }
    }

    render() {
        return (
            <div className="UserPanel">
                <div className="UserPanel-Tools">
                    <div className="NotificationIcon-Holder">
                        <div className="NotificationIconHolder">
                            <svg className="Icon" viewBox="0 0 24 24">
                                <svg viewBox="0 0 24 24" id="notifications">
                                    <path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.89 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"></path>
                                </svg>
                            </svg>
                            <span className="NotificationsCounter">1</span>
                        </div>
                    </div>
                    <div className={this.state.userActive ? "User User_active" : "User"} ref={(el) => {this.userPanel = el;}}>
                        <span className="User-Name" onClick={this.toggleActive}>Test Name</span>
                        <div className="User-AvatarHolder" onClick={this.toggleActive}>
                            <span className="User-Tips">My Roles</span>
                            <img className="User-Avatar" src={avatarImg} alt="Test ava"/>
                        </div>
                        <div className="User-Box">
                            <div className="User-Wrapper">
                                {LINKS.map((item, idx) => (
                                    <div className="User-Item" key={idx}>
                                        <p className="User-Text">
                                            <a href={item.url} {...item.args}>{item.name}</a>
                                        </p>
                                        {item.extraItem}
                                    </div>
                                ))}
                            </div>
                        </div>
                </div>
            </div>

            </div>
        );
    }
}

export default UserPanel;
