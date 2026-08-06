(function(){
  const noop=()=>{};
  function latLng(a,b){
    if(a&&typeof a==='object'&&'lat' in a)return {lat:Number(a.lat)||0,lng:Number(a.lng??a.lon)||0,distanceTo(){return 0}};
    if(Array.isArray(a))return {lat:Number(a[0])||0,lng:Number(a[1])||0,distanceTo(){return 0}};
    return {lat:Number(a)||0,lng:Number(b)||0,distanceTo(){return 0}};
  }
  function bounds(a,b){
    const pts=[]; function add(x){if(!x)return;if(Array.isArray(x)&&Array.isArray(x[0]))x.forEach(add);else pts.push(latLng(x));}
    add(a);add(b);
    return {extend(x){add(x);return this},isValid(){return pts.length>0},getCenter(){if(!pts.length)return latLng(0,0);return latLng(pts.reduce((s,p)=>s+p.lat,0)/pts.length,pts.reduce((s,p)=>s+p.lng,0)/pts.length)},getNorth(){return 1},getSouth(){return -1},getEast(){return 1},getWest(){return -1},contains(){return true},pad(){return this},toBBoxString(){return '-1,-1,1,1'}};
  }
  let id=1;
  function layer(kind,coords,opts){
    const events={}; const layers=[]; let ll=latLng(Array.isArray(coords)&&!Array.isArray(coords[0])?coords:[0,0]); let lls=coords||[]; let popup=null;
    const o={_leaflet_id:id++,_kind:kind,options:opts||{},_layers:{},
      addTo(target){try{target&&target.addLayer&&target.addLayer(o)}catch(e){}return o},remove(){return o},removeFrom(){return o},
      addLayer(x){layers.push(x);o._layers[x._leaflet_id||id++]=x;return o},removeLayer(x){const i=layers.indexOf(x);if(i>=0)layers.splice(i,1);return o},clearLayers(){layers.length=0;o._layers={};return o},eachLayer(fn){layers.slice().forEach(fn);return o},getLayers(){return layers.slice()},hasLayer(x){return layers.includes(x)},
      on(name,fn){(events[name]||(events[name]=[])).push(fn);return o},off(){return o},fire(name,data){(events[name]||[]).forEach(fn=>fn(data||{}));return o},once(name,fn){return o.on(name,fn)},
      bindPopup(content){popup={content,getContent(){return this.content},setContent(v){this.content=v;return this}};return o},getPopup(){return popup},setPopupContent(v){if(popup)popup.content=v;return o},openPopup(){return o},closePopup(){return o},isPopupOpen(){return false},unbindPopup(){popup=null;return o},
      bindTooltip(){return o},unbindTooltip(){return o},openTooltip(){return o},closeTooltip(){return o},
      setLatLng(x){ll=latLng(x);return o},getLatLng(){return ll},setLatLngs(x){lls=x;return o},getLatLngs(){return lls},getBounds(){return bounds(lls)},
      setStyle(v){Object.assign(o.options,v||{});return o},setOpacity(){return o},setIcon(){return o},bringToFront(){return o},bringToBack(){return o},redraw(){return o},
      getElement(){return null},toGeoJSON(){return {type:'Feature',properties:{},geometry:{type:kind==='polyline'?'LineString':kind==='marker'?'Point':'Polygon',coordinates:[]}}}
    }; return o;
  }
  const mapEvents={}; const mapLayers=[];
  function map(el,opts){ const container=typeof el==='string'?document.getElementById(el):el;
    const m=layer('map'); m._container=container||document.createElement('div');
    Object.assign(m,{setView(){return m},fitBounds(){return m},flyTo(){return m},panTo(){return m},invalidateSize(){return m},getCenter(){return latLng(34,-118)},getZoom(){return 10},setZoom(){return m},getBounds(){return bounds([[-1,-1],[1,1]])},getContainer(){return m._container},
      on(name,fn){(mapEvents[name]||(mapEvents[name]=[])).push(fn);return m},off(){return m},fire(name,data){(mapEvents[name]||[]).forEach(fn=>fn(data||{}));return m},
      addLayer(x){if(!mapLayers.includes(x))mapLayers.push(x);return m},removeLayer(x){const i=mapLayers.indexOf(x);if(i>=0)mapLayers.splice(i,1);return m},hasLayer(x){return mapLayers.includes(x)},eachLayer(fn){mapLayers.slice().forEach(fn);return m},
      createPane(name){const e=document.createElement('div');e.className='leaflet-pane '+name;return e},getPane(){return null},
      distance(){return 0},latLngToContainerPoint(){return {x:100,y:100}},containerPointToLatLng(){return latLng(34,-118)},mouseEventToLatLng(){return latLng(34,-118)},project(){return {x:0,y:0}},unproject(){return latLng(0,0)},
      dragging:{enable:noop,disable:noop,enabled(){return true}},doubleClickZoom:{enable:noop,disable:noop},scrollWheelZoom:{enable:noop,disable:noop}
    }); return m;
  }
  function tileLayer(){return layer('tile')}; tileLayer.wms=tileLayer;
  const L={map,layerGroup:()=>layer('group'),featureGroup:()=>layer('group'),marker:(c,o)=>layer('marker',c,o),circleMarker:(c,o)=>layer('marker',c,o),polyline:(c,o)=>layer('polyline',c,o),polygon:(c,o)=>layer('polygon',c,o),rectangle:(c,o)=>layer('polygon',c,o),circle:(c,o)=>layer('circle',c,o),geoJSON:(data,o)=>layer('geojson',[],o),tileLayer,imageOverlay:(u,b,o)=>layer('image',b,o),videoOverlay:(u,b,o)=>layer('video',b,o),latLng,latLngBounds:bounds,point:(x,y)=>({x,y}),bounds,divIcon:o=>o||{},icon:o=>o||{},canvas:o=>o||{},svg:o=>o||{},stamp:o=>o._leaflet_id||(o._leaflet_id=id++),
    DomEvent:{stopPropagation:noop,preventDefault:noop,stop:noop,disableClickPropagation:noop,disableScrollPropagation:noop,on:noop,off:noop},
    Util:{setOptions:(o,v)=>Object.assign(o.options||(o.options={}),v||{}),requestAnimFrame:fn=>setTimeout(fn,0),cancelAnimFrame:clearTimeout},
    Browser:{},CRS:{EPSG3857:{}},Control:function(){},control:function(){return layer('control')}
  };
  L.Control.extend=function(proto){function C(){}C.prototype=proto||{};return C};L.control.layers=()=>layer('control');L.control.scale=()=>layer('control');
  window.L=L;
})();
