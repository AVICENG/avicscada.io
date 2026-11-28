#define _POSIX_C_SOURCE 200809L
#include <MQTTAsync.h>
#include <jansson.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <errno.h>
#include <pthread.h>
#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#include <windows.h>
#include <rpc.h>
#else
#include <uuid/uuid.h>
#endif

#define MAX_FRAME (1024u * 1024u)
#define MAX_PAYLOAD (256u * 1024u)
#define EVENT_CAP 256u
#define QUEUE_BYTES_CAP (8u * 1024u * 1024u)
#define MAX_BINDINGS 512u
#define MAX_TOPIC 1024u

typedef struct {
    char point_id[129], topic[MAX_TOPIC];
    int qos;
} binding_t;

typedef struct event_node {
    char kind[16];
    json_t *payload;
    size_t bytes;
    struct event_node *next;
} event_node_t;

typedef struct {
    char installation_id[129], project_id[129], station_id[129];
    char driver_instance_id[129], worker_id[37];
    uint64_t generation, incoming_sequence, outgoing_sequence;
    int initialized, configured, started, stopping, connected, fatal;
    char host[256], client_id[129], tls_ca_file[512];
    int port, keepalive, mqtt_version;
    binding_t bindings[MAX_BINDINGS];
    size_t binding_count;
    MQTTAsync client;
    pthread_mutex_t queue_lock, output_lock;
    pthread_cond_t queue_cond;
    event_node_t *queue_head, *queue_tail;
    size_t queue_count, queue_bytes;
    pthread_t writer_thread;
    int writer_started;
} worker_t;

static int read_exact(FILE *stream, uint8_t *buffer, size_t length) {
    size_t done = 0;
    while (done < length) {
        size_t n = fread(buffer + done, 1, length - done, stream);
        if (!n) return 0;
        done += n;
    }
    return 1;
}
static int write_exact(FILE *stream, const uint8_t *buffer, size_t length) {
    size_t done = 0;
    while (done < length) {
        size_t n = fwrite(buffer + done, 1, length - done, stream);
        if (!n) return 0;
        done += n;
    }
    return fflush(stream) == 0;
}
static int read_frame(json_t **out) {
    uint8_t h[4]; int first = fgetc(stdin);
    if (first == EOF) return feof(stdin) ? 0 : -1;
    h[0] = (uint8_t)first;
    if (!read_exact(stdin, h + 1, 3)) return -1;
    uint32_t n = ((uint32_t)h[0] << 24) | ((uint32_t)h[1] << 16) | ((uint32_t)h[2] << 8) | h[3];
    if (!n || n > MAX_FRAME) return -1;
    char *body = malloc(n); if (!body) return -1;
    if (!read_exact(stdin, (uint8_t *)body, n)) { free(body); return -1; }
    json_error_t e; *out = json_loadb(body, n, JSON_REJECT_DUPLICATES, &e); free(body);
    return *out && json_is_object(*out) ? 1 : -1;
}
static int write_frame_locked(json_t *v) {
    char *body = json_dumps(v, JSON_COMPACT | JSON_ENSURE_ASCII);
    if (!body) return 0;
    size_t n = strlen(body);
    if (!n || n > MAX_FRAME) { free(body); return 0; }
    uint8_t h[4] = {(uint8_t)(n >> 24),(uint8_t)(n >> 16),(uint8_t)(n >> 8),(uint8_t)n};
    int ok = write_exact(stdout, h, 4) && write_exact(stdout, (uint8_t *)body, n);
    free(body); return ok;
}
static int make_uuid(char out[37]) {
#ifdef _WIN32
    UUID id; RPC_CSTR text = NULL;
    RPC_STATUS s = UuidCreate(&id);
    if ((s != RPC_S_OK && s != RPC_S_UUID_LOCAL_ONLY) || UuidToStringA(&id, &text) != RPC_S_OK || !text) return 0;
    strncpy(out, (const char *)text, 36); out[36] = 0; RpcStringFreeA(&text);
#else
    uuid_t id; uuid_generate_random(id); uuid_unparse_lower(id, out);
#endif
    return 1;
}
static void utc_now(char out[32]) {
    time_t now = time(NULL); struct tm tmv;
#ifdef _WIN32
    gmtime_s(&tmv, &now);
#else
    gmtime_r(&now, &tmv);
#endif
    strftime(out, 32, "%Y-%m-%dT%H:%M:%SZ", &tmv);
}
static const char *js(const json_t *o, const char *k) {
    json_t *v = json_object_get((json_t *)o, k);
    return json_is_string(v) ? json_string_value(v) : NULL;
}
static int ji(const json_t *o, const char *k, json_int_t *n) {
    json_t *v = json_object_get((json_t *)o, k);
    if (!json_is_integer(v)) return 0; *n = json_integer_value(v); return 1;
}
static int copy_string(char *dst, size_t cap, const char *src) {
    if (!src || !*src || strlen(src) >= cap) return 0;
    memcpy(dst, src, strlen(src) + 1); return 1;
}
static int valid_uuid(const char *s) {
    if (!s || strlen(s) != 36) return 0;
    for (int i=0;i<36;i++) {
        if (i==8||i==13||i==18||i==23) { if(s[i]!='-') return 0; }
        else if(!((s[i]>='0'&&s[i]<='9')||(s[i]>='a'&&s[i]<='f')||(s[i]>='A'&&s[i]<='F'))) return 0;
    } return 1;
}
static int contains_secret_key(json_t *v) {
    if (json_is_object(v)) {
        const char *k; json_t *child;
        json_object_foreach(v,k,child) {
            char n[96]; size_t j=0;
            for(const char *p=k;*p&&j<95;p++) if((*p>='A'&&*p<='Z')||(*p>='a'&&*p<='z')) n[j++]=(char)((*p>='A'&&*p<='Z')?*p+32:*p);
            n[j]=0;
            if(strstr(n,"password")||strstr(n,"secret")||strstr(n,"token")||strstr(n,"credential")||strstr(n,"privatekey")||strstr(n,"apikey")||contains_secret_key(child)) return 1;
        }
    } else if(json_is_array(v)) { size_t i; json_t *x; json_array_foreach(v,i,x) if(contains_secret_key(x)) return 1; }
    return 0;
}
static json_t *err_payload(const char *code,const char *msg) {
    return json_pack("{s:s,s:s}","code",code,"message",msg);
}
static int enqueue_event(worker_t *w,const char *kind,json_t *payload) {
    if (!payload) return 0;
    char *encoded=json_dumps(payload,JSON_COMPACT); size_t bytes=encoded?strlen(encoded):0; free(encoded);
    event_node_t *node=calloc(1,sizeof(*node));
    if(!node){json_decref(payload);return 0;}
    strncpy(node->kind,kind,sizeof(node->kind)-1); node->payload=payload; node->bytes=bytes;
    pthread_mutex_lock(&w->queue_lock);
    if(w->queue_count>=EVENT_CAP||bytes>MAX_FRAME||w->queue_bytes+bytes>QUEUE_BYTES_CAP) {
        w->fatal=1; pthread_cond_signal(&w->queue_cond); pthread_mutex_unlock(&w->queue_lock);
        json_decref(payload); free(node); return 0;
    }
    if(w->queue_tail) w->queue_tail->next=node; else w->queue_head=node;
    w->queue_tail=node; w->queue_count++; w->queue_bytes+=bytes;
    pthread_cond_signal(&w->queue_cond); pthread_mutex_unlock(&w->queue_lock); return 1;
}
static json_t *make_envelope(worker_t *w,const char *kind,json_t *payload,json_t *correlation) {
    char id[37],stamp[32]; if(!make_uuid(id)) return NULL; utc_now(stamp);
    json_t *e=json_object();
    json_object_set_new(e,"contract",json_string("avic.driver.ipc"));
    json_object_set_new(e,"version",json_integer(1));
    json_object_set_new(e,"message_id",json_string(id));
    json_object_set_new(e,"kind",json_string(kind));
    json_object_set_new(e,"installation_id",json_string(w->installation_id));
    json_object_set_new(e,"project_id",json_string(w->project_id));
    json_object_set_new(e,"station_id",json_string(w->station_id));
    json_object_set_new(e,"driver_instance_id",json_string(w->driver_instance_id));
    json_object_set_new(e,"worker_id",json_string(w->worker_id));
    json_object_set_new(e,"generation",json_integer((json_int_t)w->generation));
    json_object_set_new(e,"sequence",json_integer((json_int_t)++w->outgoing_sequence));
    json_object_set_new(e,"sent_at",json_string(stamp));
    json_object_set(e,"correlation_id",correlation?correlation:json_null());
    json_object_set_new(e,"payload",payload?payload:json_object());
    return e;
}
static int send_event(worker_t *w,const char *kind,json_t *payload) {
    pthread_mutex_lock(&w->output_lock);
    json_t *e=make_envelope(w,kind,payload,NULL);
    int ok=e&&write_frame_locked(e);
    if(e)json_decref(e);
    pthread_mutex_unlock(&w->output_lock);
    return ok;
}
static void *writer_main(void *arg) {
    worker_t *w=arg;
    for(;;) {
        pthread_mutex_lock(&w->queue_lock);
        while(!w->queue_head&&!w->stopping&&!w->fatal) pthread_cond_wait(&w->queue_cond,&w->queue_lock);
        if(w->fatal) {
            w->stopping=1;
            pthread_mutex_unlock(&w->queue_lock);
            send_event(w,"fault",json_pack("{s:s}","message","MQTT event queue capacity exceeded; worker fenced"));
            return NULL;
        }
        if(!w->queue_head&&w->stopping){pthread_mutex_unlock(&w->queue_lock);return NULL;}
        event_node_t *n=w->queue_head; w->queue_head=n->next;
        if(!w->queue_head)w->queue_tail=NULL;
        w->queue_count--; w->queue_bytes-=n->bytes;
        pthread_mutex_unlock(&w->queue_lock);
        if(!send_event(w,n->kind,n->payload)){free(n);return NULL;}
        free(n);
    }
}
static void on_connect_success(void *context,MQTTAsync_successData *response) {
    (void)response; worker_t *w=context; w->connected=1;
    enqueue_event(w,"status",json_pack("{s:b}","connected",1));
    for(size_t i=0;i<w->binding_count;i++) {
        MQTTAsync_responseOptions opts=MQTTAsync_responseOptions_initializer;
        opts.context=w;
        int rc=MQTTAsync_subscribe(w->client,w->bindings[i].topic,w->bindings[i].qos,&opts);
        if(rc!=MQTTASYNC_SUCCESS) enqueue_event(w,"fault",json_pack("{s:s}","message","MQTT subscribe request failed"));
    }
}
static void on_connect_failure(void *context,MQTTAsync_failureData *response) {
    (void)response; worker_t *w=context; w->connected=0;
    enqueue_event(w,"status",json_pack("{s:b}","connected",0));
    enqueue_event(w,"fault",json_pack("{s:s}","message","MQTT broker connection failed"));
}
static void on_connection_lost(void *context,char *cause) {
    worker_t *w=context; w->connected=0;
    (void)cause;
    enqueue_event(w,"status",json_pack("{s:b}","connected",0));
}
static int on_message(void *context,char *topic,int topic_len,MQTTAsync_message *message) {
    worker_t *w=context;
    if(!topic||!message||message->payloadlen<0||(size_t)message->payloadlen>MAX_PAYLOAD) {
        enqueue_event(w,"fault",json_pack("{s:s}","message","MQTT message exceeds worker payload limit"));
    } else {
        size_t tn=topic_len>0?(size_t)topic_len:strlen(topic);
        if(tn>=MAX_TOPIC) enqueue_event(w,"fault",json_pack("{s:s}","message","MQTT topic exceeds worker topic limit"));
        else {
            char topic_copy[MAX_TOPIC]; memcpy(topic_copy,topic,tn); topic_copy[tn]=0;
            const char *payload=(const char *)message->payload;
            if(memchr(payload,0,(size_t)message->payloadlen)!=NULL) {
                enqueue_event(w,"fault",json_pack("{s:s}","message","Binary MQTT payload is unsupported; UTF-8 text required"));
            } else {
                json_t *p=json_pack("{s:s,s:s,s:i,s:s,s:s}",
                    "event_class","sample","topic",topic_copy,"qos",message->qos,
                    "payload",payload?payload:"","received_at","");
                char stamp[32]; utc_now(stamp); json_object_set_new(p,"received_at",json_string(stamp));
                enqueue_event(w,"sample",p);
            }
        }
    }
    if(message) MQTTAsync_freeMessage(&message);
    if(topic) MQTTAsync_free(topic);
    return 1;
}
static void connect_client(worker_t *w) {
    MQTTAsync_connectOptions opts=MQTTAsync_connectOptions_initializer;
    opts.keepAliveInterval=w->keepalive; opts.cleansession=1;
    opts.MQTTVersion=w->mqtt_version; opts.context=w;
    opts.onSuccess=on_connect_success; opts.onFailure=on_connect_failure;
    MQTTAsync_connect(w->client,&opts);
}
static void close_client(worker_t *w) {
    if(w->client) {
        if(w->connected) {
            MQTTAsync_disconnectOptions d=MQTTAsync_disconnectOptions_initializer;
            d.timeout=1000; MQTTAsync_disconnect(w->client,&d);
        }
        MQTTAsync_destroy(&w->client);
    }
    w->connected=0;
}
static int configure(worker_t *w,json_t *p) {
    const char *host=js(p,"host"),*cid=js(p,"client_id"),*version=js(p,"mqtt_version");
    json_int_t port,keepalive;
    json_t *tls=json_object_get(p,"tls_ca_file");
    json_t *arr=json_object_get(p,"bindings");
    if(contains_secret_key(p))return 0;
    if(!host||!copy_string(w->host,sizeof(w->host),host)||!cid||!copy_string(w->client_id,sizeof(w->client_id),cid)
       ||!ji(p,"port",&port)||port<1||port>65535||!ji(p,"keepalive",&keepalive)||keepalive<10||keepalive>3600
       ||!version||(!strcmp(version,"3.1.1")?0:1)||!json_is_array(arr)||json_array_size(arr)==0||json_array_size(arr)>MAX_BINDINGS)
       return 0;
    if(!json_is_null(tls)&&tls!=NULL) return 0; /* TLS credential broker integration is a separate gate. */
    w->port=(int)port; w->keepalive=(int)keepalive; w->mqtt_version=MQTTVERSION_3_1_1;
    w->binding_count=json_array_size(arr);
    for(size_t i=0;i<w->binding_count;i++) {
        json_t *b=json_array_get(arr,i); json_int_t qos;
        const char *point=js(b,"point_id"),*topic=js(b,"topic");
        if(!point||!copy_string(w->bindings[i].point_id,sizeof(w->bindings[i].point_id),point)
          ||!topic||!copy_string(w->bindings[i].topic,sizeof(w->bindings[i].topic),topic)
          ||!ji(b,"qos",&qos)||qos<0||qos>2)return 0;
        w->bindings[i].qos=(int)qos;
    }
    return 1;
}
static int send_response(worker_t *w,json_t *request,const char *kind,json_t *payload) {
    pthread_mutex_lock(&w->output_lock);
    json_t *e=json_deep_copy(request);
    if(!e){pthread_mutex_unlock(&w->output_lock);return 0;}
    char id[37]; if(!make_uuid(id)){json_decref(e);pthread_mutex_unlock(&w->output_lock);return 0;}
    json_object_set_new(e,"message_id",json_string(id));
    json_object_set_new(e,"kind",json_string(kind));
    json_object_set_new(e,"sequence",json_integer((json_int_t)++w->outgoing_sequence));
    json_object_set_new(e,"correlation_id",json_deep_copy(json_object_get(request,"message_id")));
    json_object_set_new(e,"payload",payload?payload:json_object());
    int ok=write_frame_locked(e); json_decref(e);
    pthread_mutex_unlock(&w->output_lock); return ok;
}
static int scope_init(worker_t *w,json_t *r) {
    json_int_t g;
    return copy_string(w->installation_id,sizeof(w->installation_id),js(r,"installation_id"))
      &&copy_string(w->project_id,sizeof(w->project_id),js(r,"project_id"))
      &&copy_string(w->station_id,sizeof(w->station_id),js(r,"station_id"))
      &&copy_string(w->driver_instance_id,sizeof(w->driver_instance_id),js(r,"driver_instance_id"))
      &&copy_string(w->worker_id,sizeof(w->worker_id),js(r,"worker_id"))
      &&valid_uuid(w->worker_id)&&ji(r,"generation",&g)&&g>0&&(w->generation=(uint64_t)g)>0;
}
static int scope_check(worker_t *w,json_t *r) {
    json_int_t g;
    return ji(r,"generation",&g)&&(uint64_t)g==w->generation
      &&js(r,"installation_id")&&!strcmp(js(r,"installation_id"),w->installation_id)
      &&js(r,"project_id")&&!strcmp(js(r,"project_id"),w->project_id)
      &&js(r,"station_id")&&!strcmp(js(r,"station_id"),w->station_id)
      &&js(r,"driver_instance_id")&&!strcmp(js(r,"driver_instance_id"),w->driver_instance_id)
      &&js(r,"worker_id")&&!strcmp(js(r,"worker_id"),w->worker_id);
}
static int process(worker_t *w,json_t *r,int *quit) {
    const char *kind=js(r,"kind"),*contract=js(r,"contract");
    json_int_t version,seq; json_t *p=json_object_get(r,"payload");
    if(!kind||!contract||strcmp(contract,"avic.driver.ipc")||!ji(r,"version",&version)||version!=1
       ||!ji(r,"sequence",&seq)||seq<=0||!json_is_object(p)||!valid_uuid(js(r,"message_id")))return 0;
    if(!w->initialized){if(strcmp(kind,"initialize")||!scope_init(w,r))return 0;w->initialized=1;}
    else if(!scope_check(w,r))return 0;
    if((uint64_t)seq<=w->incoming_sequence)return 0;w->incoming_sequence=(uint64_t)seq;
    const char *reply="error"; json_t *out=NULL;
    if(!strcmp(kind,"initialize")){reply="initialized";out=json_pack("{s:s,s:i,s:s}","protocol","avic.driver.ipc","version",1,"worker_version","0.1.0");}
    else if(!strcmp(kind,"configure")) {
        if(w->started||!configure(w,p))out=err_payload("INVALID_CONFIGURATION","MQTT C Worker accepts anonymous MQTT 3.1.1 only; TLS and credentials are disabled");
        else {w->configured=1;reply="configured";out=json_pack("{s:b,s:s,s:b}","configured",1,"protocol","mqtt","write_supported",0);}
    } else if(!strcmp(kind,"start")) {
        if(!w->configured)out=err_payload("CONFIGURE_REQUIRED","Configure worker first");
        else {
            char uri[320]; snprintf(uri,sizeof(uri),"tcp://%s:%d",w->host,w->port);
            int rc=MQTTAsync_create(&w->client,uri,w->client_id,MQTTCLIENT_PERSISTENCE_NONE,NULL);
            if(rc!=MQTTASYNC_SUCCESS||!w->client)out=err_payload("MQTT_CREATE_FAILED","MQTTAsync_create failed");
            else if(MQTTAsync_setCallbacks(w->client,w,on_connection_lost,on_message,NULL)!=MQTTASYNC_SUCCESS) {
                close_client(w);out=err_payload("MQTT_CALLBACK_FAILED","MQTT callback registration failed");
            } else {
                w->started=1; connect_client(w); reply="status";
                out=json_pack("{s:s,s:b,s:b}","state","RUNNING","connected",0,"write_supported",0);
            }
        }
    } else if(!strcmp(kind,"stop")) {
        w->started=0;close_client(w);reply="status";out=json_pack("{s:s,s:b}","state","STOPPED","write_supported",0);
    } else if(!strcmp(kind,"get_status")) {
        reply="status";out=json_pack("{s:s,s:b,s:b,s:b}","state",w->started?"RUNNING":"STOPPED","configured",w->configured,"connected",w->connected,"write_supported",0);
    } else if(!strcmp(kind,"shutdown")) {
        w->started=0;close_client(w);reply="status";*quit=1;out=json_pack("{s:s,s:b}","state","STOPPED","shutdown",1);
    } else if(!strcmp(kind,"write")||!strcmp(kind,"publish"))out=err_payload("WRITE_DISABLED","MQTT publish is disabled in AVIC read-only Worker v1");
    else out=err_payload("UNKNOWN_COMMAND","Unsupported MQTT C Worker command");
    if(!out)return 0;int ok=send_response(w,r,reply,out);return ok;
}
int main(void) {
#ifdef _WIN32
    if(_setmode(_fileno(stdin),_O_BINARY)==-1||_setmode(_fileno(stdout),_O_BINARY)==-1)return 4;
#endif
    worker_t w;memset(&w,0,sizeof(w));
    pthread_mutex_init(&w.queue_lock,NULL);pthread_mutex_init(&w.output_lock,NULL);pthread_cond_init(&w.queue_cond,NULL);
    if(pthread_create(&w.writer_thread,NULL,writer_main,&w)!=0)return 5;w.writer_started=1;
    for(;;) {
        json_t *r=NULL;int status=read_frame(&r);
        if(status==0)break;if(status<0){fprintf(stderr,"MQTT C Worker: invalid IPC frame\n");break;}
        int quit=0,ok=process(&w,r,&quit);json_decref(r);
        if(!ok){fprintf(stderr,"MQTT C Worker: rejected IPC command or failed response\n");break;}
        if(quit)break;
    }
    w.started=0;close_client(&w);
    pthread_mutex_lock(&w.queue_lock);w.stopping=1;pthread_cond_broadcast(&w.queue_cond);pthread_mutex_unlock(&w.queue_lock);
    if(w.writer_started)pthread_join(w.writer_thread,NULL);
    event_node_t *n=w.queue_head;while(n){event_node_t *next=n->next;json_decref(n->payload);free(n);n=next;}
    pthread_cond_destroy(&w.queue_cond);pthread_mutex_destroy(&w.queue_lock);pthread_mutex_destroy(&w.output_lock);
    return 0;
}
