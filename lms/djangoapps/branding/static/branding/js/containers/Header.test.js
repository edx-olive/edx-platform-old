import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { mount } from 'enzyme/build';
import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';

import Header from './Header';
import { UserProfileContext } from '../context/UserProfile';
import { notificationResponse, userProfile } from '../api/mock.constants';
import BaseAPI from '../api';
import { userAPI } from '../api/user';
import {NOTIFICATIONS_URL, USER_PROFILE_URL} from '../api/urlPatterns';
import { NotificationsContext } from '../context/Notifications';
import { fsmNotifications } from '../setupTests';

const fetchMock = new MockAdapter(axios);


describe('<Header />', () => {
    test('renders without crashing', () => {
        const profileURL = BaseAPI.patchUrl(userAPI.baseUrl + USER_PROFILE_URL);
        fetchMock.onGet(profileURL).reply(200, userProfile);

        const notificationsURL = BaseAPI.patchUrl(userAPI.baseUrl + NOTIFICATIONS_URL);
        fetchMock.onGet(notificationsURL).reply(200, notificationResponse);

        mount(
            <BrowserRouter>
                <UserProfileContext.Provider value={{profile: userProfile}}>
                    <NotificationsContext.Provider value={fsmNotifications}>
                        <Header pathname='/' />
                    </NotificationsContext.Provider>
                </UserProfileContext.Provider>
            </BrowserRouter>
        );
    });
});
