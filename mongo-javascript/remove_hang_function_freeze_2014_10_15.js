/**
 * Created by wang on 14-10-15.
 */

var main = function() {
    db.function_open.find().forEach(function(obj) {
        db.function_open.update({_id: obj._id}, {$pull: {freeze: 7}})
    })
}
