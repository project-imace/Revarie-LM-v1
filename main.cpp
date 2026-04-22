#include "crow.h"

int main() {
    crow::SimpleApp app;

    CROW_ROUTE(app, "/")([](){
        return "C++ Reasoner is awake and listening!";
    });

    // Starts the C++ engine on port 9000
    app.port(9000).multithreaded().run();
    
    return 0;
}
