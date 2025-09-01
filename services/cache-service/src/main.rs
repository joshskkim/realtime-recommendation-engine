use warp::Filter;
use cache_service::handlers::{get_cache, update_cache};

#[tokio::main]
async fn main() {
    env_logger::init();

    let get_route = warp::path!("cache" / String)
        .and(warp::get())
        .and_then(get_cache);

    let update_route = warp::path!("cache" / String)
        .and(warp::post())
        .and(warp::body::json())
        .and_then(update_cache);

    let routes = get_route.or(update_route);

    warp::serve(routes)
        .run(([0, 0, 0, 0], 7000))
        .await;
}
