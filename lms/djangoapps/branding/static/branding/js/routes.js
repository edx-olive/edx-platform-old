const routes = [
    {
        'path': '/home',
        'title': 'Home',
        'inMenu': true,
        'observable': true,
        'context': {'noPopup': false}
    },
    {
        'path': 'http://courses/pathway',
        'title': 'My Pathway',
        'inMenu': true,
    },
    {
        'path': 'http://courses/',
        'title': 'Course Catalog',
        'inMenu': true,
    },
    {
        'path': 'http://connect.amat.com/',
        'title': 'Connect',
        'inMenu': true,
        'args': {'target': '_blank'},
        // TODO: maybe it's better to introduce smth like `external` flag here
        'observable': true,
        'context': {}
    },
];

export default routes;
