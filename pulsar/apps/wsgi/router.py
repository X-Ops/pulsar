from inspect import isfunction

from pulsar import HttpException

from .route import Route

__all__ = ['Router', 'route']

           
class Router(object):
    '''A WSGI application which handle multiple routes.'''
    default_content_type=None
    routes = []
    def __init__(self, rule, *routes, **handlers):
        self.route = Route(rule)
        self.routes = list(self.routes)
        for handle, callable in handlers.items():
            if not hasattr(self, handle) and hasattr(callable, '__call__'):
                setattr(self, handle, callable)
        
    def __repr__(self):
        return self.route.__repr__()
        
    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO') or '/'
        path = path[1:]
        router_args = self.resolve(path)
        if router_args:
            router, args = router_args
            request = WsgiRequest(environ, start_response, args)
            method = request.method
            callable = getattr(router, method, None)
            if callable is None:
                raise HttpException(status=405,
                                    msg='Method "%s" not allowed' % method)
            return callable(request)
        
    def resolve(self, path, urlargs=None):
        urlargs = urlargs if urlargs is not None else {}
        match = self.route.match(path)
        if match is None:
            return
        if '__remaining__' in match:
            for handler in self.routes:
                match = handler.route.match(path)
                if match is None:
                    continue
                remaining_path = match.pop('__remaining__','')
                urlargs.update(match)
                view_args = handler.resolve(remaining_path, urlargs)
                if view_args:
                    return view_args
        else:
            return self, match
    

class route(object):
    
    def __init__(self, route, method=None):
        '''Create a new Router'''
        self.router = route
        
    def __call__(self, func):
        '''func could be an unbound method of a Router class or a standard
python function.'''
        method = func.__name__.split('_')[0]
        if isfunction(func):
            pass
        else:
            cls = func.__objclass__
            self.router = self._get_router(cls)
            #self.router.routes.append()
            
    def _get_router(self, cls):
        for router in cls.routers:
            if router.path == route:
                return router
        router = Router(self.router)
        cls.routers.append(router)
        return router