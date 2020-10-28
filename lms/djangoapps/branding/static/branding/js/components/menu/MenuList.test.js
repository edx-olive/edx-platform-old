import React from 'react';

import {mount} from 'enzyme';

import MenuList from './MenuList';


// eslint-disable-next-line no-undef
describe('<MenuList />', () => {
    // eslint-disable-next-line no-undef
    test('renders without crashing', () => {
        const items = [];
        mount(<MenuList isOpen={true} items={items} path="/" pathname="/" />);
    });
});
