import React, {Component} from 'react';
import { UserProfileContext } from '../../context/UserProfile';
import { TeamContext } from '../../context/Team';
import NotificationsDropdown from './NotificationsDropdown';

export const avatarImg = "https://s3-us-west-2.amazonaws.com/pathway-frontend-assets/placeholder.png";
const defaultArgs = {'target': '_blank', rel: 'noopener noreferrer', className: 'User-Link'};
const teamListCount = array => {
  if (array) {
    return array.length
  } else {
    return 0
  }}

const LINKS = [
    {
        name: 'My role (Edit roles)',
        url: 'http://myrole',
        external: true,
        args: defaultArgs
    },
    {
        name: 'Help desk',
        url: 'http://amat.service-now.com/help?id=help_kb_article&sys_id=08d4292ddb442f44df64dd90cf9619b7',
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
            NotificationsDropdownOpen: false,
        };

        this.toggleActive = this.toggleActive.bind(this);
        this.closeUserPanel = this.closeUserPanel.bind(this);
        this.getUserAvatar = this.getUserAvatar.bind(this);
        this.toggleDropdown = this.toggleDropdown.bind(this);
        this.closeDropdown = this.closeDropdown.bind(this);
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

    getUserAvatar(profile) {
      if (profile) {
        return profile.imageSrc || avatarImg
      }
      return avatarImg
    }

    toggleDropdown() {
        if (!this.state.NotificationsDropdownOpen) {
          document.addEventListener('click', this.closeDropdown, false);
        } else {
          document.removeEventListener('click', this.closeDropdown, false);
        }

        this.setState(prevState => ({
            NotificationsDropdownOpen: !prevState.NotificationsDropdownOpen,
        }));
    }

    closeDropdown(e) {
        if (this.node.contains(e.target)) return;

        this.toggleDropdown();
    }

    render() {
        return (
            <div className="UserPanel">
                <UserProfileContext.Consumer>
                    { ({profile}) =>
                    <div className="UserPanel-Tools">
                        <TeamContext.Consumer>
                        { ({team}) => (
                          team &&
                          <div className={this.state.NotificationsDropdownOpen ? "NotificationIcon-Holder is-open" : "NotificationIcon-Holder"} ref={node => { this.node = node; }}>
                            <div
                                className={teamListCount(team.teamList) < 1 ? "NotificationIconHolder not-clickable" : "NotificationIconHolder"}
                                onClick={teamListCount(team.teamList) < 1 ? null : this.toggleDropdown}
                            >
                                <svg className="Icon" viewBox="0 0 24 24">
                                    <svg viewBox="0 0 24 24" id="notifications">
                                        <path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.89 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"></path>
                                    </svg>
                                </svg>
                                <span className="User-Tips">Notifications</span>
                                <span className={teamListCount(team.teamList) < 1 ? "NotificationsCounter is-hidden" : "NotificationsCounter"}>
                                    {teamListCount(team.teamList)}
                                </span>
                            </div>
                            <NotificationsDropdown />
                          </div>
                        )}
                        </TeamContext.Consumer>
                        <div className={this.state.userActive ? "User User_active" : "User"} ref={(el) => {this.userPanel = el;}}>
                            <div className="User-AvatarHolder" onClick={this.toggleActive}>
                                <span className="User-Tips">My Roles</span>
                                <img className="User-Avatar" src={this.getUserAvatar(profile)} alt="Test ava"/>
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
                    }
                </UserProfileContext.Consumer>
            </div>
        );
    }
}

export default UserPanel;
